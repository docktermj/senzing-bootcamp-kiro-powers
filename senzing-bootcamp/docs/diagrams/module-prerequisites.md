# Module Prerequisites

This diagram shows which modules depend on which. Use it to understand skip paths and what carries forward.

```mermaid
graph TD
    M1[Module 1: Business Problem] --> M4[Module 4: Data Collection]
    M2[Module 2: SDK Setup] --> M3[Module 3: System Verification]
    M2 --> M6[Module 6: Data Processing]
    M3 --> M4
    M4 --> M5[Module 5: Data Quality & Mapping]
    M5 --> M6
    M6 --> M7[Module 7: Query, Visualize, and Discover]

    M7 --> M8[Module 8: Performance Testing & Benchmarking]
    M8 --> M9[Module 9: Security Hardening]
    M9 --> M10[Module 10: Monitoring & Observability]
    M10 --> M11[Module 11: Package & Deploy]

    style M1 fill:#fff3e0
    style M2 fill:#e1f5fe
    style M3 fill:#e8f5e9
    style M4 fill:#fff3e0
    style M5 fill:#fff3e0
    style M6 fill:#e8f5e9
    style M7 fill:#e8f5e9
    style M8 fill:#fce4ec
    style M9 fill:#fce4ec
    style M10 fill:#fce4ec
    style M11 fill:#fce4ec
```

## Learning Paths

| Track | Modules | Color |
|-------|---------|-------|
| Core Bootcamp (recommended) | 1 → 2 → 3 → 4 → 5 → 6 → 7 | Orange → Blue → Green |
| Advanced Topics (not recommended for bootcamp) | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 | All |

Module 2 (SDK Setup) is auto-inserted before any module that needs the SDK.

## Key Skip Points

- Have Senzing Generic Entity Specification (SGES) data? Skip ahead to Module 6
- SDK already installed? Module 2 auto-detects and skips
- Already verified your setup? Skip Module 3 with an explicit "skip verification" request
- Not deploying to production? Core Bootcamp ends after Module 7 (Modules 8-11 are Advanced Topics)
