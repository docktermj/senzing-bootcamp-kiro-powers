# Common Mistakes and How to Avoid Them

This guide covers the most frequent bootcamp-operational mistakes, with real examples and fixes. For Senzing-specific issues (attribute names, SDK methods, error codes, performance tuning), ask the agent — it uses MCP tools to provide current, authoritative guidance.

## Data Preparation Mistakes

### Loading raw data without mapping

Your source data needs to be transformed into the correct format before loading. Skipping Module 5 means the engine can't recognize your fields.

What to do: Complete Module 5 (Data Quality & Mapping) for each data source before loading.

### Using too few sample records

Testing with 2-3 records doesn't produce meaningful entity resolution results. You need enough records to create entity clusters.

What to do: Use 50-200 records for demos (Module 3) and 100-1000 for quality testing (Module 5).

### Ignoring data quality scores below 70%

Proceeding with low-quality data produces poor matches. Missing names, inconsistent formats, and duplicate records all hurt results.

What to do: Check `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for what each score means and how to improve.

### Using /tmp or system directories for project files

All project files must stay in the working directory. Using `/tmp`, `%TEMP%`, or `~/Downloads` causes files to disappear.

What to do: Use `data/`, `src/`, `docs/`, `config/`, `database/` directories within your project.

### Senzing-specific data preparation issues

Issues like incorrect attribute names, wrong configuration formats, or unsupported field mappings change across SDK versions.

What to do: Ask the agent for help. It will use MCP tools (`mapping_workflow`, `search_docs`, `get_sdk_reference`) to provide current attribute names, configuration formats, and mapping guidance.

## Loading Mistakes

### Skipping database backup before loading

If a load goes wrong, you need to restore. Without a backup, you start from scratch.

What to do: Run `python3 scripts/backup_project.py` before every load operation.

### Senzing-specific loading issues

Questions about database performance limits, record processing queues, or engine behavior depend on your SDK version and deployment configuration.

What to do: Ask the agent for help. It will use MCP tools (`search_docs`, `explain_error_code`) to provide current guidance on database sizing, queue processing, and loading best practices for your setup.

## Query and Validation Mistakes

### Expecting perfect results immediately

Entity resolution is iterative. First results often need mapping adjustments, quality improvements, or additional data sources.

What to do: Use the iterate-vs-proceed decision gates in Modules 5 and 8 to decide when results are good enough.

### Senzing-specific query issues

Questions about which API methods to use, how to query entities, or how to export results depend on your SDK version and language.

What to do: Ask the agent for help. It will use MCP tools (`get_sdk_reference`, `search_docs`, `find_examples`) to provide current API guidance, correct method signatures, and working code examples.

## Production Mistakes

### Deploying without performance testing

What works with 500 records may not work with 500,000. Performance characteristics change dramatically at scale.

What to do: Complete Module 9 (Performance Testing) before production. See `docs/guides/PERFORMANCE_BASELINES.md` for expected throughput.

### No disaster recovery plan

Data loss without backups means reloading everything from scratch — which can take hours or days at production scale.

What to do: Follow the DR guidance in Module 11 Step 15. Implement the 3-2-1 backup rule.

---

See also: [FAQ](FAQ.md) | [Quality Scoring](QUALITY_SCORING_METHODOLOGY.md) | [Performance Baselines](PERFORMANCE_BASELINES.md)
