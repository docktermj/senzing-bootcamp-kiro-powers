# Senzing Bootcamp - Frequently Asked Questions

## General

### What is this bootcamp?

A guided discovery of how to use Senzing for entity resolution. It's not a race — take it slow, read what the bootcamp tells you, and ask questions at any point. You'll finish with running code that serves as the foundation for your real-world use of Senzing.

### How long does the bootcamp take?

It depends on the path you choose and the complexity of your data. There are no time limits — go at your own pace.

### Can I skip modules?

Yes. Have Senzing Entity Specification (SGES) data? Skip Module 5. SDK installed? Skip Module 2. Single source? Skip Module 7. Not deploying to production? Skip 9-12.

### What's the difference between senzing-bootcamp and senzing powers?

senzing-bootcamp is a structured 11-module curriculum (Modules 1-11). The senzing power is a quick reference. Both use the same MCP server.

### Where can I find definitions for Senzing terms?

See `docs/guides/GLOSSARY.md` for terms like Entity Specification, DATA_SOURCE, RECORD_ID, entity resolution, features, and more. You can also ask the agent to explain any term at any time.

## Getting Started

### How do I start?

Say "start the bootcamp". The agent creates your project structure and guides you through each module.

### What are the prerequisites?

Required: Python 3 (for the power's utility scripts), a supported language runtime for your bootcamp code (Python, Java, C#, Rust, or TypeScript/Node.js), git, curl. Optional: PostgreSQL. Python 3 is needed regardless of your chosen bootcamp language — it runs the power's scripts (status, validation, backup, etc.). Prerequisites are checked automatically when you start the bootcamp — the agent will tell you if anything's missing.

### Do I need a Senzing license?

Here's what you need to know: the Senzing SDK includes a built-in evaluation license limited to **500 records** — no license file required. This is enough for the bootcamp's demo modules and small datasets. If you load more than 500 records, the SDK returns a **SENZ9000** error at record 501.

For larger datasets, you need a custom license file. Email <support@senzing.com> to request a free evaluation license (typically 1–2 business days, 30–90 day validity). For production licenses, contact <sales@senzing.com>.

**If you receive a Base64-encoded license key**, decode it before placing it as `licenses/g2.lic`:

```bash
# Linux / macOS
echo '<BASE64_STRING>' | base64 --decode > licenses/g2.lic
```

```powershell
# Windows (PowerShell)
[System.Convert]::FromBase64String('<BASE64_STRING>') |
  Set-Content -Path licenses\g2.lic -AsByteStream
```

Verify the decoded file is binary (not text):

```bash
file licenses/g2.lic
```

**Never paste a license key into the chat** — always save it to `licenses/g2.lic`. See `licenses/README.md` for full details on license types, placement, and troubleshooting.

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

Run `python3 scripts/status.py`.

### Can I go back to a previous module?

Yes. The bootcamp is iterative.

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

The bootcamp applies language-appropriate coding standards based on your chosen language. See `docs/policies/CODE_QUALITY_STANDARDS.md` for details. Install the Code Style Check hook for automated checking.

### Which hooks should I install?

Hooks are installed automatically when you start the bootcamp. To reinstall or add hooks later, run `python3 scripts/install_hooks.py`.

## Backup and Recovery

### How do I backup?

Say "backup my project" (with hook installed), or run `python3 scripts/backup_project.py`.

### How do I restore?

```text
python3 scripts/restore_project.py backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip
```

## Troubleshooting

### MCP server isn't connecting?

Check internet, verify firewall allows `mcp.senzing.com:443`, check `senzing-bootcamp/mcp.json`, restart Kiro. If you're behind a corporate proxy, set `HTTPS_PROXY` in your environment. See `steering/common-pitfalls.md` for details.

### Getting a SENZ error code?

Use the MCP tool: `explain_error_code("SENZ0005")`. It covers 456 error codes with causes and resolutions.

### Files created in wrong location?

Review `docs/policies/FILE_STORAGE_POLICY.md` and relocate files to the correct directories.

### What if I run out of disk space during loading?

Stop the loading program, free disk space (clear `data/temp/`, remove old backups from `backups/`, or move the database to a larger volume), then resume or restart loading. The `backup-before-load` hook helps you recover if the database is corrupted.

### Can I run multiple bootcamp projects on the same machine?

Yes. Each project has its own directory with its own `database/G2C.db`, `config/`, and `src/`. They don't interfere with each other as long as you use project-local paths (which the FILE_STORAGE_POLICY enforces).

### What if my data has non-English names?

Senzing handles non-Latin characters (Cyrillic, CJK, Arabic, etc.) natively. During Module 5 (Data Quality & Mapping), the agent will use `search_docs(query="globalization")` for character set guidance. Make sure your source files are UTF-8 encoded — see the encoding guidance in `steering/module-05-data-quality-mapping.md`.

### What if my internet connection drops during an MCP call?

The agent will retry once automatically. If it still fails, you'll be told the MCP server isn't responding. You can continue working on non-MCP tasks (documentation, data collection, code review) and retry when connectivity returns. See the MCP Failure Recovery section in `steering/agent-instructions.md`.

### For Senzing-specific questions

Use the MCP `search_docs` tool — it searches indexed Senzing documentation and always has current information.

## Feedback

Say "power feedback" at any time. The agent guides you through documenting issues and suggestions. Your feedback is saved to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md` — see that file for the template format and submission instructions.

## Data Visualization

You can ask the agent to visualize data as a web page at any point — entity resolution results, quality analysis, match explanations, performance benchmarks. The agent will generate a self-contained HTML file you can open in your browser. The agent will also offer this at key moments (after the demo, after quality analysis, after validation, after performance testing).
