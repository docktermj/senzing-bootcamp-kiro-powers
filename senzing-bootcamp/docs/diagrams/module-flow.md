# Senzing Boot Camp - Module Flow Diagram

## Complete Module Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    SENZING BOOT CAMP MODULES                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   MODULE 0 (Optional)│
│    Quick Demo        │
│    10-15 minutes     │
│                      │
│  • Sample data       │
│  • Live resolution   │
│  • See results       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 1        │
│  Business Problem    │
│    20-30 minutes     │
│                      │
│  • Define problem    │
│  • Design patterns   │
│  • Cost estimation   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 2        │
│  Data Collection     │
│  10-15 min/source    │
│                      │
│  • Identify sources  │
│  • Collect data      │
│  • Track lineage     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 3        │
│   Data Quality       │
│  15-20 min/source    │
│                      │
│  • Quality scoring   │
│  • Completeness      │
│  • Consistency       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 4        │
│   Data Mapping       │
│   1-2 hrs/source     │
│                      │
│  • Transform data    │
│  • Map attributes    │
│  • Validate format   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 5        │
│    SDK Setup         │
│   30 min - 1 hour    │
│                      │
│  • Install SDK       │
│  • Configure DB      │
│  • Verify install    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 6        │
│  Single Source Load  │
│   30 min/source      │
│                      │
│  • Load one source   │
│  • Verify results    │
│  • Generate stats    │
└──────────┬───────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│      MODULE 7        │  │   Skip if single     │
│  Multi-Source Orch.  │  │   source only        │
│      1-2 hours       │  └──────────────────────┘
│                      │
│  • Dependencies      │
│  • Load order        │
│  • Parallel loading  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 8        │
│ Query & Validation   │
│      1-2 hours       │
│                      │
│  • Create queries    │
│  • UAT testing       │
│  • Validate results  │
└──────────┬───────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│      MODULE 9        │  │   Skip if not        │
│ Performance Testing  │  │   production         │
│      1-2 hours       │  └──────────────────────┘
│                      │
│  • Benchmarking      │
│  • Optimization      │
│  • Scalability       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     MODULE 10        │
│ Security Hardening   │
│      1-2 hours       │
│                      │
│  • Secrets mgmt      │
│  • Encryption        │
│  • PII handling      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     MODULE 11        │
│     Monitoring       │
│      1-2 hours       │
│                      │
│  • Logging           │
│  • Metrics           │
│  • Alerting          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     MODULE 12        │
│     Deployment       │
│      2-3 hours       │
│                      │
│  • Package code      │
│  • Multi-env config  │
│  • Deploy artifacts  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   🎉 COMPLETE! 🎉    │
│                      │
│  Production-ready    │
│  entity resolution   │
│  system              │
└──────────────────────┘
```

## Learning Paths

### Path A: Quick Demo (10 minutes)

```text
Module 0 → Done
```

### Path B: Fast Track (30 minutes)

```text
Module 5 → Module 6 → Done
(For users with SGES-compliant data)
```

### Path C: Complete Beginner (2-3 hours)

```text
Module 1 → Module 2 → Module 3 → Module 4 →
Module 5 → Module 6 → Module 8 → Done
```

### Path D: Full Production (10-18 hours)

```text
Module 0 → Module 1 → Module 2 → Module 3 → Module 4 →
Module 5 → Module 6 → Module 7 → Module 8 → Module 9 →
Module 10 → Module 11 → Module 12 → Done
```

## Module Dependencies

```text
Module 0: No dependencies
Module 1: No dependencies
Module 2: Requires Module 1
Module 3: Requires Module 2
Module 4: Requires Module 3
Module 5: Requires Module 4 (or SGES data)
Module 6: Requires Module 5
Module 7: Requires Module 6 (optional if single source)
Module 8: Requires Module 6 or 7
Module 9: Requires Module 8 (optional)
Module 10: Requires Module 9 (optional)
Module 11: Requires Module 10 (optional)
Module 12: Requires Module 11 (optional)
```

## Skip Conditions

```text
┌─────────────────────────────────────────────────────────┐
│ Can I skip this module?                                 │
├─────────────────────────────────────────────────────────┤
│ Module 0: Yes (but recommended for first-timers)        │
│ Module 1: No (unless you know your problem well)        │
│ Module 2: No (unless data already collected)            │
│ Module 3: No (unless quality already validated)         │
│ Module 4: Yes (if data is SGES-compliant)               │
│ Module 5: Yes (if Senzing already installed)            │
│ Module 6: No (core loading module)                      │
│ Module 7: Yes (if single source only)                   │
│ Module 8: No (must validate results)                    │
│ Module 9: Yes (if not production or perf not critical)  │
│ Module 10: Yes (if internal use only)                   │
│ Module 11: Yes (if basic monitoring sufficient)         │
│ Module 12: Yes (if not deploying to production)         │
└─────────────────────────────────────────────────────────┘
```

## Time Estimates

```text
┌──────────────────────────────────────────────────────────┐
│ Module                    │ Time Estimate                │
├──────────────────────────────────────────────────────────┤
│ Module 0: Quick Demo      │ 10-15 minutes                │
│ Module 1: Business        │ 20-30 minutes                │
│ Module 2: Collection      │ 10-15 min per source         │
│ Module 3: Quality         │ 15-20 min per source         │
│ Module 4: Mapping         │ 1-2 hours per source         │
│ Module 5: SDK Setup       │ 30 minutes - 1 hour          │
│ Module 6: Loading         │ 30 minutes per source        │
│ Module 7: Orchestration   │ 1-2 hours                    │
│ Module 8: Queries         │ 1-2 hours                    │
│ Module 9: Performance     │ 1-2 hours                    │
│ Module 10: Security       │ 1-2 hours                    │
│ Module 11: Monitoring     │ 1-2 hours                    │
│ Module 12: Deployment     │ 2-3 hours                    │
├──────────────────────────────────────────────────────────┤
│ TOTAL (all modules)       │ 10-18 hours                  │
└──────────────────────────────────────────────────────────┘
```

## Module Outputs

```text
Module 0  → Demo results, understanding of entity resolution
Module 1  → docs/business_problem.md
Module 2  → data/raw/* files, docs/data_source_evaluation.md
Module 3  → Data quality reports
Module 4  → src/transform/* programs, data/transformed/* files
Module 5  → Installed SDK, configured database
Module 6  → Loaded data, loading statistics
Module 7  → Multi-source orchestration scripts
Module 8  → src/query/* programs, UAT results
Module 9  → Performance benchmarks, optimization recommendations
Module 10 → Security configuration, compliance documentation
Module 11 → Monitoring dashboards, alerting rules
Module 12 → Deployment artifacts, runbooks
```

## Progress Tracking

Check your progress:

```bash
./scripts/status.sh
```

View detailed progress:

```bash
cat docs/guides/PROGRESS_TRACKER.md
```

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
