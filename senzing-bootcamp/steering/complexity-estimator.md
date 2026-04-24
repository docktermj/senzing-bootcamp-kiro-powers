---
inclusion: manual
---

# Data Source Complexity Estimator

Score each data source on 6 dimensions (1-3 points each), then use the total to estimate time.

## Scoring

| Dimension | 1 pt (Simple) | 2 pts (Medium) | 3 pts (Complex) |
| --------- | ------------- | --------------- | ---------------- |
| Format | CSV, JSON, single table | Multiple tables, XML, API | Nested JSON, multiple APIs, streams |
| Volume | <10K records | 10K-100K records | >100K records |
| Quality | Clean, few nulls | Some inconsistencies | Messy, many nulls |
| Mapping | Fields map 1:1 to Entity Specification | Some field combinations | Extensive transformation/parsing |
| Structure | Flat, one entity type | Some nesting, 2 types | Hierarchical, multiple types |
| Access | Local file, direct DB | API with docs, VPN | Complex API, auth issues, rate limits |

## Time Estimates by Score

| Score | Complexity | Module 4 (Mapping) | Module 5 (Loading) | Approach |
| ----- | ---------- | ------------------ | ------------------ | -------- |
| 6-9 | Low ✅ | 1-2 hours | 30 min | Quick mapping, minimal cleansing, one session |
| 10-14 | Medium ⚠️ | 2-4 hours | 1-2 hours | Plan structure carefully, incremental testing, may need iterations |
| 15-18 | High 🔴 | 4-8 hours | 2-8 hours | Break into sub-tasks, quality first, phased approach (subset first) |

## Risk Factors (Add Extra Time)

| Risk | Extra Time |
| ---- | ---------- |
| No sample data available | +1-2 hours |
| Data owner unavailable | +1-2 hours |
| Compliance requirements (PII, HIPAA) | +1-2 hours |
| First time using Senzing | +1-2 hours |
| Limited sample data (<100 records) | +0.5-1 hour |
| Unclear business requirements | +0.5-1 hour |
| Legacy system with poor docs | +0.5-1 hour |

## Optimization for High Complexity

- Phased: start with subset of fields, add incrementally, validate each step
- Quality first: clean data before mapping, fix source if possible
- Sampling: test with 100 → 1K → 10K → full dataset
- For large volume: batch processing, parallel loading, monitor resources

## Quick Examples

| Source | Format | Volume | Quality | Mapping | Structure | Access | Score | Estimate |
| ------ | ------ | ------ | ------- | ------- | --------- | ------ | ----- | -------- |
| Customer CSV | 1 | 1 | 1 | 1 | 1 | 1 | 6 (Low) | 1-2h |
| CRM Database | 2 | 2 | 2 | 2 | 2 | 1 | 11 (Med) | 2-4h |
| Legacy API | 3 | 3 | 3 | 3 | 3 | 3 | 18 (High) | 4-8h |
