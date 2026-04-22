# Module Prerequisites

This diagram shows which modules depend on which. Use it to understand skip paths and what carries forward.

```mermaid
graph TD
    M0[Module 0: Set Up SDK] --> M1[Module 1: Quick Demo]
    M0 --> M6[Module 6: Load Single Data Source]

    M2[Module 2: Business Problem] --> M3[Module 3: Data Collection Policy]
    M3 --> M4[Module 4: Data Quality]
    M4 --> M5[Module 5: Map Your Data]
    M5 --> M6

    M6 --> M7[Module 7: Multi-Source Orchestration]
    M6 --> M8[Module 8: Query, Visualize & Validate Results]
    M7 --> M8

    M8 --> M9[Module 9: Performance Testing & Benchmarking]
    M9 --> M10[Module 10: Security Hardening]
    M10 --> M11[Module 11: Monitoring & Observability]
    M11 --> M12[Module 12: Package & Deploy]

    style M0 fill:#e1f5fe
    style M1 fill:#e8f5e9
    style M2 fill:#fff3e0
    style M3 fill:#fff3e0
    style M4 fill:#fff3e0
    style M5 fill:#fff3e0
    style M6 fill:#e8f5e9
    style M7 fill:#e8f5e9
    style M8 fill:#e8f5e9
    style M9 fill:#fce4ec
    style M10 fill:#fce4ec
    style M11 fill:#fce4ec
    style M12 fill:#fce4ec
```

## Learning Paths

| Path | Modules | Color |
|------|---------|-------|
| A — Quick Demo | 0 → 1 | Blue → Green |
| B — Fast Track | 5 → 6 → 8 | Orange → Green |
| C — Complete Beginner | 2 → 3 → 4 → 5 → 6 → 8 | Orange → Green |
| D — Full Production | 0 → 1 → 2 → ... → 12 | All |

Module 0 (SDK Setup) is auto-inserted before any module that needs the SDK.

## Key Skip Points

- Have SGES data? Skip to Module 5
- SDK already installed? Module 0 auto-detects and skips
- Single source only? Skip Module 7
- Not deploying to production? Stop after Module 8
