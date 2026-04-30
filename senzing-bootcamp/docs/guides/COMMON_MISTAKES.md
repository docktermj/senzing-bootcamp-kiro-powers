# Common Mistakes and How to Avoid Them

This guide covers the most frequent mistakes bootcampers make, with real examples and fixes. For agent-specific troubleshooting, the agent uses `steering/common-pitfalls.md` automatically.

## Data Preparation Mistakes

### Loading raw data without mapping

Your source data needs to be transformed into Senzing Entity Specification (SGES) format before loading. Skipping Module 5 means Senzing can't recognize your fields.

What to do: Complete Module 5 (Data Quality & Mapping) for each data source before loading.

### Using too few sample records

Testing with 2-3 records doesn't produce meaningful entity resolution results. You need enough records to create entity clusters.

What to do: Use 50-200 records for demos (Module 3) and 100-1000 for quality testing (Module 5).

### Ignoring data quality scores below 70%

Proceeding with low-quality data produces poor matches. Missing names, inconsistent formats, and duplicate records all hurt results.

What to do: Check `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for what each score means and how to improve.

### Guessing Senzing attribute names

Senzing has 100+ attributes across 30+ feature types. Guessing names like "FULL_NAME" instead of "NAME_FULL" causes silent failures.

What to do: Always use the `mapping_workflow` MCP tool. Never hand-code attribute names.

### Using /tmp or system directories for project files

All project files must stay in the working directory. Using `/tmp`, `%TEMP%`, or `~/Downloads` causes files to disappear.

What to do: Use `data/`, `src/`, `docs/`, `config/`, `database/` directories within your project.

### Constructing engine configuration JSON manually

The engine configuration format changes between SDK versions. Hand-crafting it leads to subtle errors.

What to do: Use `sdk_guide(topic='configure')` to get the correct configuration for your platform and version.

## Loading Mistakes

### Loading 5,000+ records on SQLite

SQLite is single-writer and slows significantly as the database grows. Beyond ~1,000 records, loading becomes painfully slow.

What to do: Stay under 1,000 records on SQLite. Migrate to PostgreSQL for larger volumes (see `docs/guides/PERFORMANCE_BASELINES.md`).

### Skipping database backup before loading

If a load goes wrong, you need to restore. Without a backup, you start from scratch.

What to do: Run `python3 scripts/backup_project.py` before every load operation.

### Not processing the redo queue

After loading, Senzing queues re-evaluations for cross-record relationships. Skipping redo processing means incomplete entity resolution.

What to do: Always drain the redo queue after loading. The agent handles this in Modules 6 and 7.

## Query and Validation Mistakes

### Iterating over entity IDs instead of record IDs

You know your record IDs (from your source data). You don't know Senzing's internal entity IDs. Guessing entity ID ranges misses records.

What to do: Iterate over your loaded records using `get_entity_by_record_id(data_source, record_id)`.

### Using exportJSONEntityReport for production queries

The export API is designed for bulk extraction, not production queries. It doesn't scale and can't be filtered.

What to do: Use per-entity queries (`get_entity_by_record_id`, `search_by_attributes`) instead.

### Expecting perfect results immediately

Entity resolution is iterative. First results often need mapping adjustments, quality improvements, or additional data sources.

What to do: Use the iterate-vs-proceed decision gates in Modules 5 and 8 to decide when results are good enough.

## Production Mistakes

### Deploying without performance testing

What works with 500 records may not work with 500,000. Performance characteristics change dramatically at scale.

What to do: Complete Module 9 (Performance Testing) before production. See `docs/guides/PERFORMANCE_BASELINES.md` for expected throughput.

### No disaster recovery plan

Data loss without backups means reloading everything from scratch — which can take hours or days at production scale.

What to do: Follow the DR guidance in Module 11 Step 15. Implement the 3-2-1 backup rule.

---

See also: [FAQ](FAQ.md) | [Offline Mode](OFFLINE_MODE.md) | [Quality Scoring](QUALITY_SCORING_METHODOLOGY.md) | [Performance Baselines](PERFORMANCE_BASELINES.md)
