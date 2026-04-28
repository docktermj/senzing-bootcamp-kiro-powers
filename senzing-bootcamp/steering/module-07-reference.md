---
inclusion: manual
---

# Module 7: Multi-Source Reference Material

> Reference material for Module 7: Multi-Source Orchestration. Load this file for source ordering examples, conflict resolution guidance, error handling procedures, and troubleshooting.

## Source Ordering Examples

### Customer 360 (Quality-First)

```text
Load order:
1. CUSTOMERS_CRM (50K records, 92% quality) — best data, establishes entity baseline
2. ECOMMERCE_ACCTS (35K records, 85% quality) — matches against CRM entities
3. SUPPORT_TICKETS (20K records, 78% quality) — links to existing entities

Why: CRM has the most complete records (name + email + phone + address). Loading it first means Senzing builds strong initial entities. Subsequent sources match against this high-quality baseline.
```

### Compliance Screening (Reference-First)

```text
Load order:
1. WATCHLISTS (10K records) — reference data, must be present before screening
2. INTERNAL_CUSTOMERS (100K records) — screen against watchlists
3. THIRD_PARTY_DATA (50K records) — additional screening coverage

Why: Watchlists are reference data that other sources screen against. Loading them first ensures every subsequent record is checked against the complete watchlist.
```

## Conflict Resolution

Senzing uses **observation-based resolution** — it retains all observations from all sources rather than picking a "winner." When records from different sources conflict, Senzing does not overwrite one with the other. Instead, the resolved entity contains all observations, and consuming applications decide which to use.

> **Agent instruction:** When a bootcamper asks about conflicting records, use
> `search_docs(query="entity resolution conflicts", version="current")` to retrieve current Senzing guidance.

**Common conflict scenarios:**

1. **Different addresses**: Customer has address A in CRM and address B in E-commerce. Senzing retains both addresses on the resolved entity. The entity has two address observations — neither is "wrong."

2. **Different phone numbers**: CRM has a work phone, Support has a mobile phone. Both are retained. The entity has multiple phone observations.

3. **Different name spellings**: "Robert Johnson" in CRM, "Bob Johnson" in E-commerce. Senzing matches on name features (it knows Robert/Bob are variants). Both name observations are retained on the entity.

**Example scenario:**

```text
Source 1 (CRM):     {"DATA_SOURCE":"CRM", "RECORD_ID":"C001", "NAME_FULL":"John Smith", "ADDR_FULL":"123 Main St", "PHONE_NUMBER":"555-0101"}
Source 2 (ECOM):    {"DATA_SOURCE":"ECOM", "RECORD_ID":"E001", "NAME_FULL":"John A Smith", "ADDR_FULL":"456 Oak Ave", "EMAIL_ADDRESS":"john@email.com"}

Resolved entity:    ENTITY_ID: 1
                    Records: CRM:C001, ECOM:E001
                    Names: "John Smith", "John A Smith"
                    Addresses: "123 Main St", "456 Oak Ave"
                    Phones: "555-0101"
                    Emails: "john@email.com"
```

Both records contribute to the entity. Nothing is lost or overwritten.

> **Agent instruction:** Offer visualization: "👉 Would you like me to create a visualization showing how your entities connect across sources?" If yes, use `reporting_guide(topic='graph', version='current')` for the pattern.

## Error Handling and Recovery

### Pre-Load Validation Checklist

Run this checklist before starting orchestration:

1. ✅ All JSONL files in `data/transformed/` are valid (non-empty, valid JSON per line)
2. ✅ Every record has `DATA_SOURCE` and `RECORD_ID` fields
3. ✅ DATA_SOURCE names match the Senzing engine configuration (from Module 2)
4. ✅ RECORD_IDs are unique within each DATA_SOURCE
5. ✅ Database backup exists (`python scripts/backup_project.py`)
6. ✅ No JSONL files contain records with mismatched DATA_SOURCE values

### Per-Source Failure Isolation

When one source fails during orchestration, the agent should:

1. Log the error with source name, record number, and error message
2. Use `explain_error_code(error_code="<code>", version="current")` to diagnose
3. Continue loading remaining sources (do not stop the entire orchestration)
4. Report the failure in the final summary
5. Document the error in `docs/loading_strategy.md`

### Common Error Scenarios

| Error | Diagnosis | Fix |
| ----- | --------- | --- |
| Invalid records (malformed JSON, missing required fields) | Use `analyze_record` on a sample record from the failing source | Fix the transformation program in `src/transform/`, re-run on the source, reload |
| Duplicate RECORD_IDs across sources | Two sources use the same RECORD_ID values (e.g., both start at "1") | RECORD_IDs only need to be unique within a DATA_SOURCE — this is usually not an error. If IDs collide within the same DATA_SOURCE, prefix with source identifier |
| DATA_SOURCE name mismatch | The DATA_SOURCE in records does not match the engine configuration | Verify DATA_SOURCE names against Module 2 setup. Fix in the transformation program |
| Transformation errors (wrong attribute names, missing mappings) | Use `analyze_record` to validate a sample record | Re-run Module 5 mapping workflow for the affected source |

### Recovery Options

IF a source fails during orchestration, THEN present these three options:

1. **Skip and continue**: Mark the source as failed, continue loading remaining sources. Come back to the failed source after fixing the issue. Best when other sources are independent.
2. **Retry after fix**: Pause orchestration, fix the issue (e.g., repair transformation), retry the failed source. Best when the fix is quick and obvious.
3. **Restore and restart**: Restore the database from backup (`python scripts/restore_project.py`), fix the issue, restart orchestration from the beginning. Best when the failure may have corrupted data.

👉 "Source [name] failed with [error]. Would you like to skip it and continue with the remaining sources, fix the issue and retry, or restore from backup and start over?"

WAIT for response.

## Troubleshooting Quick Reference

> **Agent instruction:** Use this section for quick diagnosis. If the issue is not covered here, load `common-pitfalls.md` for the full Module 7 pitfall table.

| Issue | Diagnosis | Resolution |
| ----- | --------- | ---------- |
| Low cross-source match rates | Check Module 5 quality scores for each source. Review Module 5 mapping consistency — are the same fields mapped to the same Senzing attributes across sources? Use `get_sdk_reference(topic='why')` to examine match details for specific entities | Improve data quality in weak sources, align attribute mappings across sources, ensure name/address/phone/email fields are mapped consistently |
| Unexpected entity merges | Two entities from different sources merged that should not have. Use the SDK "why" method to see which features caused the match | Check for overly generic features (e.g., common names without other distinguishing attributes). Review data quality — are placeholder values ("N/A", "Unknown") causing false matches? |
| Slow loading with multiple sources | Check total record count, database type (SQLite vs PostgreSQL), and parallelism level | SQLite slows significantly beyond ~1,000 total records. Reduce parallelism to 1-2 workers. For larger volumes, recommend PostgreSQL migration (Module 9) |
| Redo queue not draining | Check for errors in redo processing output. Use `explain_error_code` for any error codes | Restart the redo processor. If errors persist, check for corrupted entities and consider restoring from backup |
| Resource exhaustion (out of memory, disk full) | Monitor system resources during parallel loading. Check database file size | Reduce max parallel loaders. Free disk space or move database to larger volume. Increase available memory |
| Source ordering affects resolution quality | Compare entity counts and match rates after loading in different orders | Apply the ordering heuristics from Step 4. In general, loading higher-quality sources first produces better results. If results are significantly different, the data quality gap between sources is large — address in Module 5 |

### Performance Benchmarks

Set expectations based on database type:

- **SQLite (bootcamp default)**: ~50-200 records/second single-threaded. Slows as database grows. Suitable for ≤1,000 total records across all sources.
- **PostgreSQL**: ~500-2,000 records/second with multi-threading. Scales to millions of records. Recommend migration when total records exceed 1,000 or when loading takes more than a few minutes.

If the bootcamper is experiencing slow loading, suggest: "Loading is slow because SQLite doesn't handle concurrent writes well. For the bootcamp, let's work with a smaller subset. When you're ready for production volumes, Module 9 covers PostgreSQL migration."

## Common Issues

- **Dependency cycles**: Flag to bootcamper, explain that Senzing handles load order gracefully — load the higher-quality source first
- **Resource exhaustion**: Reduce parallelism, check disk space, consider PostgreSQL
- **Slow performance**: Optimize transformations, reduce record count for bootcamp, or use PostgreSQL
- **Missing sources**: Check Module 5 — all sources must be mapped before orchestration
- **Inconsistent mappings**: Different sources map the same real-world field to different Senzing attributes — re-run Module 5 for consistency
