---
inclusion: manual
---

# Module 6: Data Processing — Reference Material

> **Agent instruction:** Only present multi-source reference material when the bootcamper has 2 or more data sources. For single-source bootcampers, skip this file entirely.

## Source Ordering Heuristics

Apply in priority order:

1. **Reference before transactional** — Load reference data (watchlists, catalogs) before transactional data
2. **Quality-first** — Highest-quality source first for a strong entity baseline
3. **Attribute-density-first** — Sources with more matching attributes create better initial entities
4. **Volume-first** — When quality is similar, load the larger source first

### Examples

**Customer 360 (Quality-First):** CRM (50K, 92%) → E-commerce (35K, 85%) → Support (20K, 78%). CRM has the most complete records, establishing strong initial entities.

**Compliance Screening (Reference-First):** Watchlists (10K) → Internal Customers (100K) → Third-Party (50K). Watchlists must be present before screening.

## Orchestration Patterns

1. **Sequential:** Simple, predictable. Load sources one at a time in order.
2. **Parallel (independent):** Fast for independent sources. Run up to 3 workers concurrently.
3. **Dependency-aware:** Recursively load dependencies before each source.
4. **Pipeline:** Producer-consumer with thread-safe queue for streaming large datasets.

## Error Handling Strategies

1. **Fail Fast:** Stop all loading on first error
2. **Continue on Error:** Log errors, continue with other sources
3. **Retry with Backoff:** Exponential backoff (1s, 2s, 4s, 8s)
4. **Partial Success:** Mark successful sources, retry only failed ones

## Conflict Resolution

Senzing uses **observation-based resolution** — retains all observations from all sources rather than picking a "winner." Conflicting records are not overwritten; the resolved entity contains all observations.

**Common scenarios:** Different addresses → both retained. Different phones → both retained. Name spelling variants → Senzing matches on features, retains all variants.

> **Agent instruction:** Use `search_docs(query="entity resolution conflicts", version="current")` for current guidance.

## Troubleshooting Quick Reference

| Issue | Diagnosis | Resolution |
| ----- | --------- | ---------- |
| Low cross-source match rates | Check quality scores, mapping consistency, use SDK "why" method | Improve quality, align attribute mappings |
| Unexpected entity merges | Use SDK "why" method to see which features caused match | Check for overly generic features, placeholder values |
| Slow loading | Check record count, DB type, parallelism | Use PostgreSQL, reduce parallelism |
| Redo queue not draining | Check for errors, use `explain_error_code` | Restart redo processor |
| Resource exhaustion | Monitor resources during parallel loading | Reduce workers, free disk, add memory |
| All records become one entity | Entity count = 1 | Check RECORD_ID uniqueness, verify distinguishing features |
| No duplicates found | Entity count = record count | Check matching features present, review quality scores |

## Performance Benchmarks

- **SQLite:** ~50–200 records/second single-threaded. Suitable for ≤1,000 total records.
- **PostgreSQL:** ~500–2,000 records/second multi-threaded. Scales to millions.

## Pre-Load Validation Checklist

1. ✅ All JSONL files in `data/transformed/` are valid
2. ✅ Every record has `DATA_SOURCE` and `RECORD_ID`
3. ✅ DATA_SOURCE names match engine configuration
4. ✅ RECORD_IDs unique within each DATA_SOURCE
5. ✅ Database backup exists
6. ✅ No mismatched DATA_SOURCE values in JSONL files

## Per-Source Failure Isolation

When one source fails: log error with source name and message, use `explain_error_code`, continue loading remaining sources, report in final summary, document in `docs/loading_strategy.md`.

## Common Error Scenarios

| Error | Diagnosis | Fix |
| ----- | --------- | --- |
| Invalid records | Use `analyze_record` on sample | Fix transformation, re-run, reload |
| Duplicate RECORD_IDs across sources | Usually not an error — IDs only need uniqueness within a DATA_SOURCE | Prefix with source ID if colliding within same DATA_SOURCE |
| DATA_SOURCE name mismatch | Doesn't match engine config | Verify against Module 2 setup, fix transformation |
| Transformation errors | Wrong attribute names | Re-run Module 5 mapping for affected source |

## Common Issues

- **Dependency cycles**: Load higher-quality source first
- **Resource exhaustion**: Reduce parallelism, check disk, consider PostgreSQL
- **Missing sources**: Check Module 5 — all sources must be mapped first
- **Inconsistent mappings**: Re-run Module 5 for consistency
