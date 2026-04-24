# Senzing Bootcamp - Module Flow Diagram

> **Viewing:** These diagrams use text-based ASCII art and are viewable in any text editor or markdown viewer. No special extensions required.

## Complete Module Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    SENZING BOOTCAMP MODULES                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│      MODULE 0        │
│    SDK Setup         │
│                      │
│  • Install SDK       │
│  • Configure DB      │
│  • Verify install    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   MODULE 1 (Optional)│
│    Quick Demo        │
│                      │
│  • Sample data       │
│  • Live resolution   │
│  • See results       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 2        │
│  Business Problem    │
│                      │
│  • Define problem    │
│  • Design patterns   │
│  • Cost estimation   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 3        │
│  Data Collection     │
│                      │
│  • Identify sources  │
│  • Collect data      │
│  • Track lineage     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 4        │
│ Data Quality &       │
│ Mapping              │
│                      │
│  • Quality scoring   │
│  • Completeness      │
│  • Consistency       │
│  • Transform data    │
│  • Map attributes    │
│  • Validate format   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 5        │
│  Single Source Load  │
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
│      MODULE 6        │  │   Skip if single     │
│  Multi-Source Orch.  │  │   source only        │
│                      │
│  • Dependencies      │
│  • Load order        │
│  • Parallel loading  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 7        │
│ Query & Visualize    │
│                      │
│  • Create queries    │
│  • Overlap reports   │
│  • Visualizations    │
└──────────┬───────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│      MODULE 8        │  │   Skip if not        │
│ Performance Testing  │  │   production         │
│                      │
│  • Benchmarking      │
│  • Optimization      │
│  • Scalability       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 9        │
│ Security Hardening   │
│                      │
│  • Secrets mgmt      │
│  • Encryption        │
│  • PII handling      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     MODULE 10        │
│     Monitoring       │
│                      │
│  • Logging           │
│  • Metrics           │
│  • Alerting          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     MODULE 11        │
│     Deployment       │
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

### Path A: Quick Demo

```text
Module 1 → Done
```

### Path B: Fast Track

```text
Module 0 → Module 4 → Module 5 → Module 7 → Done
(For users with Senzing Entity Specification (SGES)-compliant data)
```

### Path C: Complete Beginner

```text
Module 2 → Module 3 → Module 4 →
Module 0 → Module 5 → Module 7 → Done
```

### Path D: Full Production

```text
Module 0 → Module 1 → Module 2 → Module 3 → Module 4 →
Module 5 → Module 6 → Module 7 → Module 8 →
Module 9 → Module 10 → Module 11 → Done
```

## Module Dependencies

```text
Module 0: No dependencies
Module 1: No dependencies
Module 2: No dependencies
Module 3: Requires Module 2
Module 4: Requires Module 3
Module 5: Requires Module 0 (SDK) and Module 4 (or Entity Specification data)
Module 6: Requires Module 5 (optional if single source)
Module 7: Requires Module 5 or 6
Module 8: Requires Module 7 (optional)
Module 9: Requires Module 8 (optional)
Module 10: Requires Module 9 (optional)
Module 11: Requires Module 10 (optional)
```

## Skip Conditions

```text
┌─────────────────────────────────────────────────────────┐
│ Can I skip this module?                                 │
├─────────────────────────────────────────────────────────┤
│ Module 0: Yes (if Senzing already installed)            │
│ Module 1: Yes (but recommended for first-timers)        │
│ Module 2: No (unless you know your problem well)        │
│ Module 3: No (unless data already collected)            │
│ Module 4: No (unless quality already validated and      │
│           data is Entity Specification-compliant)        │
│ Module 5: No (core loading module)                      │
│ Module 6: Yes (if single source only)                   │
│ Module 7: No (must validate results)                    │
│ Module 8: Yes (if not production or perf not critical)  │
│ Module 9: Yes (if internal use only)                    │
│ Module 10: Yes (if basic monitoring sufficient)         │
│ Module 11: Yes (if not deploying to production)         │
└─────────────────────────────────────────────────────────┘
```

## Module Outputs

```text
Module 0  → Installed SDK, configured database
Module 1  → Demo results, understanding of entity resolution
Module 2  → docs/business_problem.md
Module 3  → data/raw/* files, docs/data_source_locations.md
Module 4  → Data quality reports, src/transform/* programs, data/transformed/* files
Module 5  → Loaded data, loading statistics
Module 6  → Multi-source orchestration scripts
Module 7  → src/query/* programs, visualizations
Module 8  → Performance benchmarks, optimization recommendations
Module 9  → Security configuration, compliance documentation
Module 10 → Monitoring dashboards, alerting rules
Module 11 → Deployment artifacts, runbooks
```

## Progress Tracking

Check your progress:

```text
python scripts/status.py
```

View detailed progress:

```bash
cat docs/guides/PROGRESS_TRACKER.md
```

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
