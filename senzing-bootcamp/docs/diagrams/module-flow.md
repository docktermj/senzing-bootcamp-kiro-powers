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
│      MODULE 3        │
│  System Verification │
│                      │
│  • TruthSet data     │
│  • Live resolution   │
│  • Verify entity     │
│    counts            │
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
│  • Transform data    │
│  • Map attributes    │
│  • Optional test load│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      MODULE 6        │
│  Data Processing     │
│                      │
│  • Load all sources  │
│  • Process redo      │
│  • Validate results  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│          MODULE 7           │
│ Query, Visualize, and        │
│ Discover                     │
│                              │
│  • Create queries            │
│  • Overlap reports           │
│  • Visualizations            │
└──────────────┬───────────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│      MODULE 8        │  │   Core Bootcamp      │
│ Performance Testing  │  │   ends here          │
│ & Benchmarking       │  │   (Modules 8-11 are  │
│                      │  │   Advanced Topics)   │
│  • Benchmarking      │  └──────────────────────┘
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
│ Monitoring &         │
│ Observability        │
│                      │
│  • Logging           │
│  • Metrics           │
│  • Alerting          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     MODULE 11        │
│  Package & Deploy    │
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

### Core Bootcamp (recommended)

```text
Module 1 → Module 2 → Module 3 → Module 4 → Module 5 →
Module 6 → Module 7 → Done
```

### Advanced Topics (not recommended for bootcamp)

```text
Module 1 → Module 2 → Module 3 → Module 4 → Module 5 →
Module 6 → Module 7 → Module 8 → Module 9 →
Module 10 → Module 11 → Done
```

## Module Dependencies

```text
Module 1:  No dependencies
Module 2:  No dependencies
Module 3:  Requires Module 2 (SDK)
Module 4:  Requires Module 1 and Module 3
Module 5:  Requires Module 4
Module 6:  Requires Module 2 (SDK) and Module 5
Module 7:  Requires Module 6
Module 8:  Requires Module 7
Module 9:  Requires Module 8
Module 10: Requires Module 9
Module 11: Requires Module 10
```

## Skip Conditions

```text
┌─────────────────────────────────────────────────────────┐
│ Can I skip this module?                                 │
├─────────────────────────────────────────────────────────┤
│ Module 1:  No (unless you know your problem well)       │
│ Module 2:  Yes (if Senzing already installed)           │
│ Module 3:  Only on explicit "skip verification" request │
│            (recommended for first-timers)               │
│ Module 4:  No (unless data already collected)           │
│ Module 5:  No (unless data already Entity               │
│            Specification-compliant)                     │
│ Module 6:  No (unless data already loaded)              │
│ Module 7:  No (must validate results)                   │
│ Module 8:  Yes (not needed for POC)                     │
│ Module 9:  Yes (internal-only, no sensitive data)       │
│ Module 10: Yes (not deploying to production)            │
│ Module 11: Yes (not deploying to production)            │
└─────────────────────────────────────────────────────────┘
```

## Module Outputs

```text
Module 1  → docs/business_problem.md
Module 2  → Installed SDK, configured database
Module 3  → System verification results, visualization
Module 4  → data/raw/* files, docs/data_source_locations.md
Module 5  → Data quality reports, src/transform/* programs, data/transformed/* files
Module 6  → Loaded data, redo processing, loading statistics
Module 7  → src/query/* programs, visualizations, discovery reports
Module 8  → Performance benchmarks, optimization recommendations
Module 9  → Security configuration, compliance documentation
Module 10 → Monitoring dashboards, alerting rules, health checks
Module 11 → Deployment artifacts, CI/CD, runbooks
```

## Progress Tracking

Check your progress:

```text
python3 scripts/status.py
```

View detailed progress:

```bash
cat docs/guides/PROGRESS_TRACKER.md
```

---

**Last Updated:** 2026-06-23
**Version:** 2.0.0
