```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 1: UNDERSTAND BUSINESS PROBLEM  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 1: Understand Business Problem

> **Agent workflow:** The agent follows `steering/module-01-business-problem.md` for this module's step-by-step workflow.

## Overview

Module 1 helps you define your entity resolution problem, identify data sources, and create a clear project plan. This foundation ensures the rest of the bootcamp is tailored to your specific needs.

**Prerequisites:** None (or Module 3 complete if you did the demo)
**Output:** Business problem statement document, project directory structure, cost estimate

## Learning Objectives

By the end of this module, you will:

- Clearly articulate your entity resolution problem
- Identify all relevant data sources
- Define success criteria
- Understand project costs and ROI
- Have an organized project structure

## What You'll Do

1. Set up project directory structure
2. Initialize version control (optional)
3. Choose a design pattern (optional)
4. Answer discovery questions (one at a time)
5. Create business problem statement
6. Estimate costs and ROI
7. Update project README

## Design Pattern Gallery

Choose a pattern that matches your use case:

| Pattern                  | Use Case                | Key Matching                      |
|--------------------------|-------------------------|-----------------------------------|
| **Customer 360**         | Unified customer view   | Names, emails, phones, addresses  |
| **Fraud Detection**      | Identify fraud rings    | Names, addresses, devices, IPs    |
| **Data Migration**       | Merge legacy systems    | All available identifiers         |
| **Compliance Screening** | Watchlist matching      | Names, DOB, nationalities, IDs    |
| **Marketing Dedup**      | Eliminate duplicates    | Names, addresses, emails          |
| **Patient Matching**     | Unified medical records | Names, DOB, SSN, MRNs             |
| **Vendor MDM**           | Clean vendor master     | Company names, tax IDs, addresses |
| **Claims Fraud**         | Detect staged accidents | Names, vehicles, providers        |
| **KYC/Onboarding**       | Verify identity         | Names, DOB, SSN, gov IDs          |
| **Supply Chain**         | Unified supplier view   | Company names, GLNs, tax IDs      |

Selecting a pattern helps pre-fill answers and set realistic expectations.

## Discovery Questions

The agent will ask these questions ONE AT A TIME:

### Question 1: What problem are you trying to solve?

Examples:

- Deduplication (remove duplicate records)
- Data matching (link records across systems)
- Identity verification (confirm person/organization identity)
- Fraud detection (find suspicious patterns)
- Relationship discovery (find connections between entities)
- Master data management (create golden records)

### Question 2: What data sources are involved?

For each source, identify:

- Name (e.g., "Customer CRM", "Vendor Database")
- Type (database, CSV, API, Excel, etc.)
- Approximate record count
- Update frequency (static, daily, real-time)
- Access method (how to get the data)

### Question 3: What types of entities?

- People (customers, employees, patients)
- Organizations (vendors, suppliers, companies)
- Both
- Other (vehicles, products, locations)

### Question 4: What matching criteria matter most?

Examples:

- Names (person names, company names)
- Addresses (physical, mailing)
- Contact info (phone, email)
- Identifiers (SSN, tax ID, account numbers)
- Dates (DOB, registration date)
- Other attributes (specific to your domain)

### Question 5: What's the desired outcome?

Consider:

- Output format (master list, API, reports, database export)
- Use case (one-time cleanup, ongoing sync, real-time lookup)
- Integration needs (standalone or integrated with other systems)
- Success metrics (how will you measure success?)

## Project Directory Structure

The Senzing Bootcamp agent will automatically create this organized directory structure for you:

```text
my-senzing-project/
├── .git/                          # Version control (optional)
├── .gitignore                     # Exclude sensitive data
├── .env.example                   # Template for environment variables
├── .env                           # Actual environment variables (not in git)
├── data/
│   ├── raw/                       # Original source data
│   ├── transformed/               # Senzing-formatted JSON
│   ├── samples/                   # Sample data for testing
│   └── backups/                   # Database backups
├── src/
│   ├── quickstart_demo/           # Module 3 demo code (optional)
│   ├── transform/                 # Transformation programs
│   ├── load/                      # Loading programs
│   ├── query/                     # Query programs
│   └── utils/                     # Shared utilities
├── tests/                         # Test files
├── docs/
│   ├── business_problem.md        # This module's output
│   ├── data_source_evaluation.md  # Module 4 output
│   ├── mapping_specifications.md  # Module 5 output
│   ├── query_specifications.md    # Module 8 output
│   └── lessons_learned.md         # Post-project retrospective
├── config/                        # Configuration files
├── logs/                          # Log files
├── monitoring/                    # Monitoring and dashboards
├── scripts/                       # Shell scripts for automation
└── README.md                      # Project description
```

## Version Control Setup

The agent will check if your directory is already a git repository:

```bash
git rev-parse --git-dir 2>/dev/null
```

If not, you'll be asked: "Would you like to initialize this as a git repository?"

Benefits of using git:

- Track changes throughout the bootcamp
- Revert mistakes easily
- Collaborate with team members
- Document progress with commits

## Business Problem Statement Document

The agent will create `docs/business_problem.md`:

```markdown
# Business Problem Statement

**Date:** [Current date]
**Project:** [Project name]
**Design Pattern:** [Pattern name if selected, or "Custom"]

## Problem Description
[One sentence description]

## Use Case Category
[Customer 360 / Fraud Detection / etc.]

## Design Pattern Reference
[If a pattern was selected, include customizations]

## Data Sources
1. **[Source name]**
   - Type: [Database/CSV/API/etc.]
   - Records: ~[count]
   - Entity type: [People/Organizations/Both]
   - Update frequency: [Static/Daily/Real-time]
   - Access: [How to access]

## Entity Types
[People / Organizations / Both / Other]

## Key Matching Criteria
- **[Attribute 1]** (High priority) - [Why important]
- **[Attribute 2]** (Medium priority) - [Why important]

## Success Criteria
- [Measurable outcome 1]
- [Measurable outcome 2]

## Desired Output
**Format:** [Master list / API / Reports / Database export]
**Use case:** [One-time / Ongoing / Real-time]
**Integration:** [Standalone / Integrated with [systems]]

## Timeline
**Target completion:** [Date]
**Key milestones:** [List]

## Notes
[Any additional context, constraints, or considerations]
```

## Cost Estimation

The agent will help estimate:

### Data Source Records (DSRs)

- Count total records across all data sources
- Determine Senzing license tier
- Estimate annual license cost

### Infrastructure Costs

- Database (SQLite free, PostgreSQL $200-5000/month)
- Application servers ($100-800/month)
- Storage ($50-300/month)
- Monitoring ($50-500/month)

### ROI Calculation

Identify benefits:

- Cost savings (reduced duplicates, improved efficiency)
- Revenue opportunities (better targeting, faster onboarding)
- Risk reduction (fraud prevention, compliance)

The agent will create `docs/cost_estimate.md` with detailed calculations.

## README Update

The agent will update your project README with:

- Project overview
- Business problem summary
- Data sources list
- Setup instructions (to be filled in later modules)

## Success Criteria

✅ Project directory structure created
✅ Version control initialized (if desired)
✅ Business problem clearly defined
✅ All data sources identified
✅ Success criteria documented
✅ Cost estimate completed
✅ `docs/business_problem.md` created
✅ README.md updated
✅ User confirms accuracy

## Common Pitfalls

### Too Vague

❌ "I want to clean my data"
✅ "I want to deduplicate customer records across CRM and e-commerce systems"

### Missing Data Sources

❌ "I have customer data"
✅ "I have CRM (500K records), e-commerce (300K), and support tickets (200K)"

### Unclear Success Criteria

❌ "Better data quality"
✅ "Reduce duplicate mailings by 80%, saving $50K/year"

### Unrealistic Timeline

❌ "Complete in 2 hours"
✅ "Complete Modules 2-6 in 8-10 hours over 2 weeks"

## Tips for Success

1. **Be specific:** Vague problems lead to vague solutions
2. **Think end-to-end:** Consider the entire workflow, not just matching
3. **Start small:** Begin with 1-2 data sources, expand later
4. **Define metrics:** How will you know if it's working?
5. **Consider stakeholders:** Who needs to approve this?

## Next Steps

After completing Module 1:

- **Proceed to Module 4:** Collect actual data from identified sources
- **Review with stakeholders:** Get buy-in on problem statement and costs
- **Adjust timeline:** Based on complexity estimate

## Related Documentation

- `POWER.md` - Bootcamp overview
- `steering/module-01-business-problem.md` - Module 1 workflow
- Use MCP `search_docs` with query "pricing" for current Senzing pricing
- `docs/guides/DESIGN_PATTERNS.md` - Design pattern details

## Troubleshooting

**Not sure which pattern to choose?**

- Describe your use case to the agent
- Review the pattern gallery
- It's OK to choose "Custom" if none fit exactly

**Don't know record counts?**

- Provide rough estimates (order of magnitude)
- You can refine later in Module 4

**Multiple use cases?**

- Start with the most important one
- You can expand scope later

**Stakeholder approval needed?**

- Use the cost estimate document
- Show ROI calculations
- Reference similar use cases from pattern gallery

## Version History

- **v3.0.0** (2026-03-17): Module 1 documentation created
