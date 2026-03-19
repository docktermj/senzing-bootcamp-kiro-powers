# Senzing Boot Camp -- Executive Summary

## What It Is

The Senzing Boot Camp is a structured, hands-on training program that takes participants from zero Senzing experience to production-ready entity resolution deployments. Participants learn to identify duplicate and related records across one or more data sources using the Senzing SDK -- without machine learning models, training data, or manual rule writing. The bootcamp is taught entirely with open-source data.

## Why It Matters

Organizations routinely maintain the same customers, vendors, or entities across multiple systems -- CRM, billing, support, compliance -- with no reliable way to connect them. Senzing provides real-time entity resolution that automatically discovers which records refer to the same real-world entity, enabling a single unified view. The boot camp gives teams the skills to evaluate, integrate, and deploy this capability.

## How It Works

Attendees bring a Windows or Mac laptop and connect to a pre-configured AWS bootcamp account that provides the compute environment, Senzing SDK, and sample data. The development workflow is powered by Kiro, an AI-assisted IDE, with the Senzing MCP server connected to provide context-aware guidance, validated data mappings, and SDK code generation throughout the modules.

## What Participants Will Accomplish

- **Evaluate in hours, not weeks.** Module 0 delivers a working entity resolution demo in under 15 minutes using sample data from Las Vegas, London, or Moscow datasets.
- **Map and load data.** Modules 1--6 walk through defining the business problem, collecting source data, scoring data quality, mapping fields to the Senzing entity specification, installing the SDK, and loading a first data source.
- **Scale to multiple sources.** Modules 7--8 cover multi-source orchestration, query development, and user acceptance testing.
- **Harden for production.** Modules 9--12 address performance testing, security hardening, monitoring/observability, and deployment packaging -- including Docker, CI/CD, and Kubernetes options.

## Who Should Attend

Data engineers, integration architects, and technical leads responsible for implementing entity resolution, master data management, or data quality initiatives. Basic programming skills (Python, Java, C#, or Rust) and command-line familiarity are the only prerequisites -- no prior Senzing or ML experience is needed.

## Flexible Learning Paths

| Path | Modules | Estimated Time |
|------|---------|----------------|
| Quick Evaluation | 0, 1, 2, 4, 5, 6, 8 | 4--6 hours |
| Single-Source PoC | 1, 2, 3, 4, 5, 6, 8 | 6--8 hours |
| Multi-Source PoC | 1--8 | 8--12 hours |
| Full Production Deployment | 0--12 (all) | 10--18 hours |

Modules can be completed across multiple sessions.

---

## Prerequisites at a Glance

### What to Bring

- A Windows or Mac laptop with a modern web browser
- Internet connectivity (to reach the AWS bootcamp account)

### AWS Bootcamp Environment

Each attendee connects to a dedicated AWS bootcamp account that provides:

- Pre-installed Senzing SDK and dependencies
- Kiro IDE with the Senzing MCP server already connected
- Sample open-source datasets ready to use
- Sufficient compute, memory, and storage for all modules

### Experience

- Basic programming in at least one SDK language (Python, Java, C#, or Rust) -- Python is the bootcamp default
- Command-line navigation (`cd`, `ls`, `mkdir`, etc.)
- Familiarity with CSV and JSON formats
- No prior Senzing, ML, or DBA experience required

### Data

No data preparation is needed. All modules use open-source datasets provided in the AWS bootcamp environment.
