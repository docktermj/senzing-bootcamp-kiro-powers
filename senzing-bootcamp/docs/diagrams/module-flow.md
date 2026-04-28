# Senzing Bootcamp - Module Flow Diagram

> **Viewing:** These diagrams use text-based ASCII art and are viewable in any text editor or markdown viewer. No special extensions required.

## Complete Module Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    SENZING BOOTCAMP MODULES                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│      MODULE 1        │
│  Business Problem    │
│                      │
│  • Define problem    │
│  • Design patterns   │
│  • Cost estimation   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 2        │
│    SDK Setup         │
│                      │
│  • Install SDK       │
│  • Configure DB      │
│  • Verify install    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   MODULE 3 (Optional)│
│    Quick Demo        │
│                      │
│  • Sample data       │
│  • Live resolution   │
│  • See results       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 4        │
│  Data Collection     │
│                      │
│  • Identify sources  │
│  • Collect data      │
│  • Track lineage     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 5        │
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
│      MODULE 6        │
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
│      MODULE 7        │  │   Skip if single     │
│  Multi-Source Orch.  │  │   source only        │
│                      │
│  • Dependencies      │
│  • Load order        │
│  • Parallel loading  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 8        │
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
│      MODULE 9        │  │   Skip if not        │
│ Performance Testing  │  │   production         │
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
Module 3 → Done
```

### Path B: Fast Track

```text
Module 2 → Module 5 → Module 6 → Module 8 → Done
(For users with Senzing Entity Specification (SGES)-compliant data)
```

### Path C: Complete Beginner

```text
Module 1 → Module 4 → Module 5 →
Module 2 → Module 6 → Module 8 → Done
```

### Path D: Full Production

```text
Module 1 → Module 2 → Module 3 → Module 4 → Module 5 →
Module 6 → Module 7 → Module 8 → Module 9 →
Module 10 → Module 11 → Module 12 → Done
```

## Module Dependencies

```text
Module 1: No dependencies
Module 2: No dependencies
Module 3: No dependencies
Module 4: Requires Module 1
Module 5: Requires Module 4
Module 6: Requires Module 2 (SDK) and Module 5 (or Entity Specification data)
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
│ Module 1: No (unless you know your problem well)        │
│ Module 2: Yes (if Senzing already installed)            │
│ Module 3: Yes (but recommended for first-timers)        │
│ Module 4: No (unless data already collected)            │
│ Module 5: No (unless quality already validated and      │
│           data is Entity Specification-compliant)        │
│ Module 6: No (core loading module)                      │
│ Module 7: Yes (if single source only)                   │
│ Module 8: No (must validate results)                    │
│ Module 9: Yes (if not production or perf not critical)  │
│ Module 10: Yes (if internal use only)                   │
│ Module 11: Yes (if basic monitoring sufficient)         │
│ Module 12: Yes (if not deploying to production)         │
└─────────────────────────────────────────────────────────┘
```

## Module Outputs

```text
Module 1  → docs/business_problem.md
Module 2  → Installed SDK, configured database
Module 3  → Demo results, understanding of entity resolution
Module 4  → data/raw/* files, docs/data_source_locations.md
Module 5  → Data quality reports, src/transform/* programs, data/transformed/* files
Module 6  → Loaded data, loading statistics
Module 7  → Multi-source orchestration scripts
Module 8  → src/query/* programs, visualizations
Module 9  → Performance benchmarks, optimization recommendations
Module 10 → Security configuration, compliance documentation
Module 11 → Monitoring dashboards, alerting rules
Module 12 → Deployment artifacts, runbooks
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
