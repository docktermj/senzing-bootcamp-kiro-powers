# Entity Resolution Project — Executive Summary

**Date**: [date] | **Module**: [module_number] — [module_name] | **Status**: [status]

---

## Problem Statement

[problem_statement]

## Approach

[approach]

## Data Sources

[data_sources]

## Key Findings / Results

[key_findings]

## Next Steps

[next_steps]

## ROI Considerations

[roi_considerations]

---

*Generated after Module [module_number] of the Senzing Bootcamp.*

---

<!-- AGENT INSTRUCTIONS: Module-Specific Placeholder Guidance

Use the guidance below to fill the placeholders above based on which module was just completed.
Copy the template sections above into a new file, replace each placeholder with the
module-specific content described below, and save to the indicated output path.

=============================================================================
MODULE 2 — Business Problem Definition
Output: docs/stakeholder_summary_module2.md
=============================================================================

[status]        → "Problem defined, ready for data collection"
[module_number] → "2"
[module_name]   → "Business Problem Definition"

[problem_statement]
  Summarize the business problem from docs/business_problem.md in 2-3 sentences.
  Focus on the business impact: what pain point does entity resolution address?
  Example: "Customer records are duplicated across CRM and billing systems,
  causing inaccurate reporting and wasted outreach."

[approach]
  Describe the planned entity resolution approach in non-technical terms.
  Mention Senzing by name. Reference the design pattern if one was selected.
  Example: "Using Senzing entity resolution to match and deduplicate customer
  records across 3 data sources based on name, address, and email attributes."

[data_sources]
  List each identified data source with approximate record count.
  Use a simple table or bullet list. Pull from docs/business_problem.md.
  Example:
  | Source | Records | Type |
  |--------|---------|------|
  | CRM Export | ~50,000 | CSV |
  | Billing System | ~35,000 | Database |

[key_findings]
  Summarize what was discovered during problem analysis.
  Example: "Identified 3 data sources with overlapping customer records.
  Estimated 15-20% duplication rate based on preliminary analysis."

[next_steps]
  1. Collect and catalog data samples (Module 3)
  2. Evaluate data quality (Module 4)
  3. Map data to Senzing format (Module 5)
  4. Load and resolve entities (Modules 6-7)

[roi_considerations]
  Frame the expected business value. Use estimates where possible.
  Example: "Eliminating duplicate customer records is projected to reduce
  mailing costs by 15% and improve campaign targeting accuracy.
  A unified customer view enables cross-sell opportunities across channels."

=============================================================================
MODULE 8 — Query and Validation Results
Output: docs/stakeholder_summary_module8.md
=============================================================================

[status]        → "Results validated, ready for [performance testing / production planning]"
[module_number] → "8"
[module_name]   → "Query and Validation Results"

[problem_statement]
  Restate the original business problem from docs/business_problem.md.
  Add context on what has been accomplished since Module 2.
  Example: "We set out to deduplicate customer records across CRM and billing.
  Data has been collected, quality-scored, mapped, loaded, and resolved."

[approach]
  Describe what was actually done — not just planned.
  Mention record counts, data sources loaded, and resolution method.
  Example: "Loaded 85,000 records from 3 data sources into Senzing.
  Entity resolution matched records using name, address, email, and phone."

[data_sources]
  List each data source with actual loaded record counts.
  Pull from loading results and config/bootcamp_progress.json.
  Example:
  | Source | Records Loaded | Match Rate |
  |--------|---------------|------------|
  | CRM Export | 50,000 | 18% matched |
  | Billing System | 35,000 | 22% matched |

[key_findings]
  Present validation results with specific metrics.
  Pull from docs/results_validation.md and UAT results.
  Example:
  - 85,000 records resolved into 62,000 unique entities
  - 95% UAT test cases passed (45/50)
  - 2% false positive rate, 3% false negative rate
  - Cross-source matching linked 12,000 records across systems

[next_steps]
  Based on validation results and the user's bootcamp path:
  - Path B/C: "Results validated. Ready to integrate into production workflows."
  - Path D: "Proceed to performance testing (Module 9) and production hardening."

[roi_considerations]
  Quantify actual results against the original business case.
  Example: "Entity resolution identified 23,000 duplicate records (27% of total).
  Eliminating these duplicates is estimated to save $45,000/year in mailing costs
  and reduce customer service lookup time by 30%."

=============================================================================
MODULE 12 — Deployment and Packaging
Output: docs/stakeholder_summary_module12.md
=============================================================================

[status]        → "Deployed to [environment]" or "Packaged and deployment-ready"
[module_number] → "12"
[module_name]   → "Deployment and Packaging"

[problem_statement]
  Restate the business problem with full project context.
  Frame it as a completed initiative.
  Example: "Customer record duplication across 3 systems was causing $60K/year
  in wasted outreach and inaccurate reporting. This project deployed an
  automated entity resolution system to eliminate duplicates at scale."

[approach]
  Describe the deployed architecture in non-technical terms.
  Mention deployment target, method, and key infrastructure.
  Example: "Senzing entity resolution deployed on AWS using containerized
  services with PostgreSQL, automated CI/CD pipeline, monitoring dashboards,
  and security hardening. Supports real-time and batch processing."

[data_sources]
  List production data sources with volumes and integration method.
  Example:
  | Source | Records | Integration | Frequency |
  |--------|---------|-------------|-----------|
  | CRM | 50,000 | API | Real-time |
  | Billing | 35,000 | Batch | Nightly |
  | Support | 20,000 | Batch | Weekly |

[key_findings]
  Summarize production metrics and deployment outcomes.
  Pull from deployment results and monitoring baselines.
  Example:
  - System deployed to production on [date]
  - Processing 105,000 records across 3 sources
  - Average query latency: 45ms (p99: 120ms)
  - All health checks passing, zero critical alerts
  - 99.9% uptime target achievable with current architecture

[next_steps]
  1. Monitor production performance for 30 days
  2. Onboard additional data sources as identified
  3. Schedule quarterly data quality reviews
  4. Plan capacity for projected data growth

[roi_considerations]
  Present the full business case with measured results.
  Example: "The deployed system eliminates 23,000 duplicate records automatically.
  Projected annual savings: $45,000 in mailing costs, $30,000 in reduced
  manual data cleanup, and improved customer experience through unified records.
  Total first-year ROI estimated at 3.2x implementation cost."

-->
