---
inclusion: manual
---

# Module Prerequisites

## Quick Reference: Dependencies

> **Authoritative source:** The prerequisite data in this table is derived from
> `config/module-dependencies.yaml`. To update prerequisites, edit the dependency
> graph first, then run `python3 scripts/validate_dependencies.py` to verify
> consistency.

| Module                       | Requires                                                     | Skip if                                          |
|------------------------------|--------------------------------------------------------------|--------------------------------------------------|
| 1 — Business Problem         | None                                                         | —                                                |
| 2 — SDK Setup                | None (first technical module)                                | SDK already installed (verify with import check) |
| 3 — Quick Demo               | Module 2                                                     | Already familiar with Senzing                    |
| 4 — Data Collection          | Module 1                                                     | —                                                |
| 5 — Data Quality & Mapping   | Module 4, files in `data/raw/`                               | All sources Entity Specification-compliant → Module 6 |
| 6 — Load Data                | Module 2 + Module 5, transformed data in `data/transformed/` | Data already loaded → Module 7                   |
| 7 — Query & Visualize         | Module 6, no critical load errors                            | Already validated → Module 8                     |
| 8 — Performance              | Module 7, representative data loaded                         | Not needed for POC                               |
| 9 — Security                 | Module 8, compliance needs documented                        | Internal-only with no sensitive data             |
| 10 — Monitoring              | Module 9, monitoring tools selected                          | Not deploying to production                      |
| 11 — Deployment              | Module 10, all tests passing                                 | Not deploying to production                      |

## Common Blockers by Module

| Module | Blocker                         | Fix                                                                   |
|--------|---------------------------------|-----------------------------------------------------------------------|
| 2      | Missing admin access            | Request from IT                                                       |
| 2      | Insufficient disk space (<10GB) | Free space or external storage                                        |
| 2      | Network restrictions            | Work with IT to allow downloads                                       |
| 4      | Missing data access permissions | Request from data owners                                              |
| 4      | Too many sources                | Start with 1-2 most important                                         |
| 5      | Data in proprietary format      | Convert to CSV or JSON                                                |
| 5      | Unclear field meanings          | Consult data source documentation                                     |
| 6      | SDK not working                 | Return to Module 2                                                    |
| 6      | No transformed data             | Return to Module 5                                                    |
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
