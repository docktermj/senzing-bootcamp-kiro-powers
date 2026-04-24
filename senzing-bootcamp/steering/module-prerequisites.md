---
inclusion: manual
---

# Module Prerequisites

## Quick Reference: Dependencies

| Module                       | Requires                                                     | Skip if                                          |
|------------------------------|--------------------------------------------------------------|--------------------------------------------------|
| 0 — SDK Setup                | None (first module)                                          | SDK already installed (verify with import check) |
| 1 — Quick Demo               | Module 0                                                     | Already familiar with Senzing                    |
| 2 — Business Problem         | None                                                         | —                                                |
| 3 — Data Collection          | Module 2                                                     | —                                                |
| 4 — Data Quality & Mapping   | Module 3, files in `data/raw/`                               | All sources Entity Specification-compliant → Module 5 |
| 5 — Single Source Load       | Module 0 + Module 4, transformed data in `data/transformed/` | Data already loaded → Module 7                   |
| 6 — Multi-Source             | Module 5                                                     | Single data source → Module 7                    |
| 7 — Query & Validate         | Module 5 or 6, no critical load errors                       | Already validated → Module 8                     |
| 8 — Performance              | Module 7, representative data loaded                         | Not needed for POC                               |
| 9 — Security                 | Module 8, compliance needs documented                        | Internal-only with no sensitive data             |
| 10 — Monitoring              | Module 9, monitoring tools selected                          | Not deploying to production                      |
| 11 — Deployment              | Module 10, all tests passing                                 | Not deploying to production                      |

## Common Blockers by Module

| Module | Blocker                         | Fix                                                                   |
|--------|---------------------------------|-----------------------------------------------------------------------|
| 0      | Missing admin access            | Request from IT                                                       |
| 0      | Insufficient disk space (<10GB) | Free space or external storage                                        |
| 0      | Network restrictions            | Work with IT to allow downloads                                       |
| 3      | Missing data access permissions | Request from data owners                                              |
| 3      | Too many sources                | Start with 1-2 most important                                         |
| 4      | Data in proprietary format      | Convert to CSV or JSON                                                |
| 4      | Unclear field meanings          | Consult data source documentation                                     |
| 5      | SDK not working                 | Return to Module 0                                                    |
| 5      | No transformed data             | Return to Module 4                                                    |
| 6      | First load failed               | Return to Module 5                                                    |
| 7      | Loading errors                  | Review logs, fix, reload                                              |
| 8      | No performance requirements     | Define acceptable thresholds                                          |
| 9      | Unclear security requirements   | Consult security team                                                 |
| 10     | No monitoring platform          | Select and install (Prometheus+Grafana for local, CloudWatch for AWS) |
| 11     | Tests failing                   | Fix issues, return to relevant module                                 |

## Agent Behavior

When user wants to start a module:

1. Check prerequisites in the table above
2. If not met → inform user, suggest completing prerequisite modules
3. If met → proceed
4. If user insists on skipping → warn about potential issues but allow

When user is stuck: identify which prerequisite is unmet, guide them back to complete it.
