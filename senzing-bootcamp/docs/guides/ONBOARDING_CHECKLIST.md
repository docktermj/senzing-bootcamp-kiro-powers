# Senzing Boot Camp Onboarding Checklist

Complete this checklist before starting the boot camp to ensure a smooth experience.

## Pre-Flight Checklist

### ✅ Step 1: Create Project Directory Structure

**This should be your first step!** Create the organized directory layout for your Senzing project:

- [ ] **Create project directory**

  ```bash
  mkdir my-senzing-project
  cd my-senzing-project
  ```

- [ ] **Create directory structure**

  ```bash
  mkdir -p data/{raw,transformed,samples,backups}
  mkdir -p database
  mkdir -p src/{transform,load,query,utils}
  mkdir -p tests
  mkdir -p docs/feedback
  mkdir -p config
  mkdir -p logs
  mkdir -p monitoring
  mkdir -p scripts
  ```

- [ ] **Create initial files**

  ```bash
  touch README.md
  touch .gitignore
  touch .env.example
  ```

- [ ] **Verify structure**

  ```bash
  tree -L 2  # or ls -R
  ```

Expected structure:

```text
my-senzing-project/
├── data/
│   ├── raw/
│   ├── transformed/
│   ├── samples/
│   └── backups/
├── database/
├── src/
│   ├── transform/
│   ├── load/
│   ├── query/
│   └── utils/
├── tests/
├── docs/
│   └── feedback/
├── config/
├── logs/
├── monitoring/
├── scripts/
├── README.md
├── .gitignore
└── .env.example
```

**Why first?** Having the directory structure in place ensures all generated files go to the right locations from the start.

### ✅ Step 2: System Requirements

> **Note for agents:** Do not rely on the versions listed below. During onboarding,
> always fetch the current official requirements via the Senzing MCP server:
> `search_docs(query="system requirements", version="current")`.
> The values below are a snapshot for offline reference only.

- [ ] **Operating System** — verify against [Senzing v4 System Requirements](https://www.senzing.com/docs/release/4/4_0_hw_sw)
  - Linux (Ubuntu LTS, RHEL, Debian, Amazon Linux)
  - macOS (Apple Silicon only, Limited Availability)
  - Windows (Limited Availability)

- [ ] **SDK Language** — verify minimum versions via MCP `search_docs`
  - Python: pip package manager available, virtual environment tool (venv or conda)
  - Java: Maven or Gradle available
  - C#: NuGet package manager available

- [ ] **Disk Space**
  - Minimum: 10 GB free
  - Recommended: 50 GB+ for production

- [ ] **Memory**
  - Minimum: 8 GB RAM
  - Recommended: 16 GB+ for production

### ✅ Step 3: Data Preparation

- [ ] **Data Sources Identified**
  - List of all data sources documented
  - Approximate record counts known
  - Data owners/contacts identified

- [ ] **Data Access**
  - Access to source systems confirmed
  - Credentials available (if needed)
  - Sample data extracted (100-1000 records)
  - Full data extraction plan in place

- [ ] **Data Format**
  - File formats identified (CSV, JSON, Excel, etc.)
  - Database schemas documented (if applicable)
  - API documentation available (if applicable)

- [ ] **Data Privacy**
  - PII handling requirements understood
  - Data anonymization needs identified
  - Compliance requirements documented (GDPR, HIPAA, etc.)

### ✅ Step 4: Database Setup

- [ ] **Database Choice** — verify supported versions via MCP `search_docs(query="system requirements", version="current")`
  - SQLite for evaluation (small datasets)
  - PostgreSQL for production (recommended)
  - MySQL, MSSQL, Oracle also supported — check MCP for minimum versions
  - Cloud-managed databases (AWS Aurora/RDS, Azure SQL) also supported

- [ ] **Database Access** (if using PostgreSQL/MySQL/etc.)
  - Database server available
  - Admin credentials available
  - Network access confirmed
  - Backup strategy in place

### ✅ Step 5: Development Environment

- [ ] **Code Editor/IDE**
  - VS Code, PyCharm, IntelliJ, or similar
  - Git integration available
  - Terminal access

- [ ] **Version Control**
  - Git installed
  - GitHub/GitLab/Bitbucket account (optional)
  - Understanding of basic git commands

- [ ] **Command Line**
  - Comfortable with terminal/command prompt
  - Basic shell commands (cd, ls, mkdir, etc.)
  - Ability to run scripts

### ✅ Step 6: Time and Resources

- [ ] **Time Commitment**
  - 2-3 hours for quick start (Modules 2-6, 8)
  - 10-18 hours for complete boot camp (Modules 0-12)
  - Flexible schedule for iterative work

- [ ] **Team Resources** (if applicable)
  - Data engineers available
  - Business stakeholders identified
  - IT/DevOps support for deployment

- [ ] **Budget** (if applicable)
  - Senzing license obtained or requested (see `licenses/README.md`)
  - For boot camp: Request free evaluation license from [support@senzing.com](mailto:support@senzing.com)
  - For production: Contact [sales@senzing.com](mailto:sales@senzing.com) for pricing
  - Infrastructure budget allocated
  - Timeline for procurement

### ✅ Step 7: Knowledge Prerequisites

- [ ] **Basic Programming**
  - Comfortable with Python, Java, or C#
  - Understanding of functions and classes
  - Ability to read and modify code

- [ ] **Data Concepts**
  - Understanding of CSV, JSON formats
  - Basic SQL knowledge (if using databases)
  - Familiarity with data quality concepts

- [ ] **Entity Resolution** (helpful but not required)
  - Understanding of what entity resolution is
  - Awareness of use cases (deduplication, matching, etc.)
  - Familiarity with data matching concepts

### ✅ Step 8: Documentation and Support

- [ ] **Documentation Access**
  - Senzing documentation available
  - Boot camp power installed in Kiro
  - MCP server configured

- [ ] **Support Channels**
  - Kiro agent available for guidance
  - Senzing support contact: [support@senzing.com](mailto:support@senzing.com)
  - Senzing sales contact (for licensing): [sales@senzing.com](mailto:sales@senzing.com)
  - Internal team support identified

## Quick Validation

Run these commands to verify your setup:

### Check Python

```bash
python --version  # Verify against MCP system requirements
pip --version
```

### Check Java (if using)

```bash
java -version  # Verify against MCP system requirements
mvn --version  # or gradle --version
```

### Check Git

```bash
git --version
```

### Check Disk Space

```bash
df -h  # Linux/macOS
```

### Check Memory

```bash
free -h  # Linux
vm_stat  # macOS
```

## Ready to Start?

### All Checks Complete ✅

You're ready to start the boot camp! Tell the agent:

```text
"I'm ready to start the Senzing boot camp"
```

### Some Checks Incomplete ⚠️

**Missing system requirements?**

- Install required software first

**Don't have data yet?**

- Start with Module 1 (Quick Demo) using sample data
- Prepare your data while learning

**Limited time?**

- Choose the 30-minute fast track
- Or complete modules incrementally

**Need help?**

- Ask the agent: "Help me prepare for the boot camp"
- Review `docs/guides/QUICK_START.md` for path options

## Troubleshooting

### Python Issues

```bash
# Install Python 3.10+
sudo apt install python3.11  # Ubuntu/Debian
brew install python@3.11     # macOS

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### Database Issues

```bash
# Install PostgreSQL
sudo apt install postgresql  # Ubuntu/Debian
brew install postgresql      # macOS

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
```

### Disk Space Issues

```bash
# Clean up package caches
sudo apt clean  # Ubuntu/Debian
brew cleanup    # macOS
```

## Next Steps

After completing this checklist:

1. **Choose your path**: Demo, Fast Track, or Complete
2. **Start Module 0 or 1**: Tell the agent you're ready
3. **Follow the guide**: Agent will walk you through each step
4. **Track progress**: Use `docs/guides/PROGRESS_TRACKER.md`

## Support

Need help with the checklist?

```text
"Help me check if I'm ready for the boot camp"
"What do I need to install?"
"I don't have [requirement], what should I do?"
```

---

**Version**: 1.1.0
**Last updated**: 2026-04-01
