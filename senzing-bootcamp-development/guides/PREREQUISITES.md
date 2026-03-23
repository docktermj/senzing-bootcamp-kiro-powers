# Senzing Boot Camp Prerequisites

What you need before starting the boot camp.

## Hardware

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| **RAM** | 8 GB | 16 GB+ | More helps with larger datasets and production modules |
| **Disk Space** | 10 GB free | 50 GB+ | Raw data, transformed data, and database all consume space |
| **CPU** | 2 cores | 4+ cores | Multi-threading improves loading performance |
| **Network** | Internet access | Broadband | Required for installing packages, pulling Docker images, and accessing documentation |

## Software

### Required

| Software | Minimum Version | Recommended | Purpose |
|----------|----------------|-------------|---------|
| **Operating System** | See platform list below | Linux (Ubuntu 22.04) | Senzing SDK host |
| **Git** | Any recent version | Latest | Version control for your project |

Plus **one** of the following SDK languages:

| Language | Minimum Version | Recommended |
|----------|----------------|-------------|
| **Python** | 3.8 | 3.11+ |
| **Java** | 11 | 17+ |
| **C# (.NET)** | 6.0 | 6.0+ |
| **Rust** | Stable | Latest stable |

Python is the most common choice and what the bootcamp examples default to. If using Python, you also need `pip` and the ability to create virtual environments (`python -m venv`).

### Supported Platforms

| Platform | Status |
|----------|--------|
| Ubuntu 20.04 / 22.04 | Fully supported (production and development) |
| RHEL 8 / 9 | Fully supported (production and development) |
| Debian 11+ | Fully supported (production and development) |
| macOS (Intel or ARM) | Development only |
| Windows (WSL2) | Development only |
| Docker | Fully supported (any host OS) |

### Optional but Helpful

| Software | Version | When You Need It |
|----------|---------|------------------|
| **Docker** | Any recent version | Recommended for Module 0 quick demo; required if you want to skip native Senzing installation |
| **PostgreSQL** | 11+ (14+ recommended) | Production deployments (Modules 9-12); SQLite works for evaluation |
| **tree** | Any | Handy for verifying project directory structure |

## Experience

### Required

- **Basic programming** in your chosen SDK language (Python, Java, C#, or Rust) -- you should be comfortable reading, writing, and running simple programs
- **Command line basics** -- navigating directories, running scripts, editing files (`cd`, `ls`, `mkdir`, `cat`, etc.)
- **Data format familiarity** -- understanding of CSV and JSON file formats

### Helpful but Not Required

- **SQL basics** -- useful if you choose PostgreSQL for your database
- **Docker fundamentals** -- useful if you take the containerized path
- **Git workflow** -- branching, committing, pushing
- **Data quality concepts** -- understanding of deduplication, matching, and data cleansing
- **Entity resolution concepts** -- Module 0 (quick demo) is designed to teach this from scratch

### Not Required

- Prior Senzing experience -- the bootcamp teaches everything from the ground up
- Machine learning or AI knowledge -- Senzing handles entity resolution without model training
- Database administration -- SQLite requires zero setup; PostgreSQL setup is guided

## Data Preparation

Before starting Module 1, it helps to have:

- A list of the data sources you want to resolve (e.g., CRM, billing, support tickets)
- Approximate record counts for each source
- Sample extracts (100-1,000 records) in CSV, JSON, or a similar format
- An understanding of any PII/compliance constraints (GDPR, HIPAA, etc.)

If you don't have your own data yet, Module 0 provides sample datasets so you can learn the workflow first.

## Time Commitment

| Path | Modules | Time |
|------|---------|------|
| Quick Evaluation | 0, 1, 2, 4, 5, 6, 8 | 4-6 hours |
| Single Source PoC | 1, 2, 3, 4, 5, 6, 8 | 6-8 hours |
| Multi-Source PoC | 1-8 | 8-12 hours |
| Full Production Deployment | 0-12 (all) | 10-18 hours |

Modules can be completed across multiple sessions.

## Quick Verification

Run these commands to confirm your environment is ready:

```bash
# Check Python (if using Python SDK)
python3 --version        # Expect 3.8+

# Check pip
pip3 --version

# Check Git
git --version

# Check Docker (optional)
docker --version

# Check disk space
df -h .

# Check memory
free -h                  # Linux
```

If all required checks pass, you're ready to start. See the [Onboarding Checklist](ONBOARDING_CHECKLIST.md) for a detailed step-by-step setup walkthrough.
