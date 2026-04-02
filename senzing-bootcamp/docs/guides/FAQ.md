# Senzing Boot Camp - Frequently Asked Questions

## General

### How long does the boot camp take?

- Quick Demo (Module 1): 10-15 minutes
- Fast Track (Modules 0, 6): 30 minutes
- Complete Beginner (Modules 2-6, 8): 2-3 hours
- Full Production (All Modules 0-12): 10-18 hours

### Can I skip modules?

Yes. Have SGES data? Skip Module 5. SDK installed? Skip Module 0. Single source? Skip Module 7. Not deploying to production? Skip 9-12.

### What's the difference between senzing-bootcamp and senzing powers?

senzing-bootcamp is a structured 13-module curriculum. The senzing power is a quick reference. Both use the same MCP server.

## Getting Started

### How do I start?

Say "start the boot camp". The agent creates your project structure and guides you through each module.

### What are the prerequisites?

Required: A supported language runtime (Python, Java, C#, Rust, or TypeScript/Node.js), git, curl. Optional: PostgreSQL. Run `python scripts/check_prerequisites.py` to verify.

### Do I need a Senzing license?

The agent asks about your license early in the workflow. The SDK includes built-in evaluation limits that work for the boot camp. For a full evaluation license (no limits), email <support@senzing.com> (1-2 business days). See `licenses/README.md`.

### Where should I put my files?

- Source data: `data/raw/`
- Transformed data: `data/transformed/`
- Source code: `src/`
- Scripts: `scripts/`
- Documentation: `docs/`
- Database: `database/`

See `docs/policies/FILE_STORAGE_POLICY.md`.

## Working with Modules

### How do I know which module I'm on?

Run `python scripts/status.py`.

### Can I go back to a previous module?

Yes. The boot camp is iterative.

### What if I get stuck?

1. Check module prerequisites (`module-prerequisites.md`)
2. Check `steering/common-pitfalls.md`
3. Use MCP tool `search_docs` for Senzing topics
4. Use MCP tool `explain_error_code` for SENZ errors
5. Ask the agent

## Code and Files

### Where should I put my code?

Transformation: `src/transform/`. Loading: `src/load/`. Queries: `src/query/`. Utilities: `src/utils/`. Scripts: `scripts/`. Never in the project root.

### What are the code quality standards?

The boot camp applies language-appropriate coding standards based on your chosen language. See `docs/policies/CODE_QUALITY_STANDARDS.md` for details. Install the Code Style Check hook for automated checking.

### Which hooks should I install?

Run `python scripts/install_hooks.py` for interactive installation. Recommended: Code Style Check, `backup-before-load`, `data-quality-check`, `validate-senzing-json`.

## Backup and Recovery

### How do I backup?

Say "backup my project" (with hook installed), or run `python scripts/backup_project.py`.

### How do I restore?

```text
python scripts/restore_project.py backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip
```

## Troubleshooting

### MCP server isn't connecting?

Check internet, verify firewall allows `mcp.senzing.com:443`, check `senzing-bootcamp/mcp.json`, restart Kiro.

### Getting a SENZ error code?

Use the MCP tool: `explain_error_code("SENZ0005")`. It covers 456 error codes with causes and resolutions.

### Files created in wrong location?

Review `docs/policies/FILE_STORAGE_POLICY.md` and relocate files to the correct directories.

### For Senzing-specific questions

Use the MCP `search_docs` tool — it searches indexed Senzing documentation and always has current information.

## Feedback

Say "power feedback" at any time. The agent guides you through documenting issues and suggestions.
