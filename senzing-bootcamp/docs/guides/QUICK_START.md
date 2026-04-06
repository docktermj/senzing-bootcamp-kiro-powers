# Senzing Bootcamp Quick Start

Get started with Senzing entity resolution in 30 minutes or less.

## Three Quick Start Paths

### Path A: Demo (Module 1)

**Best for:** First-time users, seeing entity resolution in action

**Prerequisite:** Module 0 (SDK Setup) must be completed first.

```bash
# 1. Ask the agent
"Let's run the quick demo with the Las Vegas dataset"

# 2. Watch entity resolution happen
# - Sample data loads
# - Duplicates are automatically resolved
# - Results show matched entities

# 3. Understand the results
# - See why records matched
# - Review confidence scores
# - Connect to your use case
```

**Time:** Quick

**Output:** Understanding of entity resolution

---

### Path B: Fast Track

**Best for:** Experienced users with SGES-compliant data

> **Agent instruction:** For Path B, offer the user two options:
>
> 1. **Fastest**: Use `sdk_guide(topic='full_pipeline', platform='<user_platform>', language='<chosen_language>', version='current')` to get install + configure + load + export in one call. This is the quickest way to see results.
> 2. **Step-by-step**: Walk through Module 0 then Module 6 separately for more control.

```bash
# 1. Define problem
"I want to deduplicate customers from my CRM"

# 2. Upload data
# Drag and drop your SGES-formatted JSON file

# 3. Install SDK and load data
# Agent uses sdk_guide(topic='full_pipeline') for fastest setup
# Or walk through Module 0 → Module 6 for step-by-step control
```

**Time:** Quick

**Output:** Working entity resolution on your data

**Requirement:** Data already in SGES format

---

### Path C: Complete Beginner

**Best for:** New users with raw data (CSV, database, etc.)

```bash
# 1. Define problem
# - Answer discovery questions
# - Identify data sources
# - Set success criteria

# 2. Collect data
# - Upload or link to data files
# - Document locations

# 3. Evaluate quality
# - Run automated quality scoring
# - Review metrics

# 4. Map data
# - Use mapping_workflow tool
# - Create transformation program
# - Validate quality

# 5. Install SDK
# - Install Senzing
# - Configure database

# 6. Load and query
# - Load data
# - Find duplicates
# - Examine results
```

**Output:** Complete working project

**Modules:** 2-6, 8 (Module 0 is auto-inserted before Module 6 for SDK setup)

---

## Choose Your Path

### I want to

**"See a demo first"** → Path A (Demo)

- Requires Module 0 (SDK Setup) first
- Then Module 1 demo

**"Get results fast"** → Path B (Fast Track)

- Skip to Module 0 (SDK Setup) then Module 6
- Requires SGES-compliant data
- SQLite for quick start

**"Learn properly"** → Path C (Complete)

- Start with Module 2

**"Build for production"** → Path D: Full Bootcamp

- Complete all modules 0-12
- Production-ready deployment
- Security, monitoring, optimization

---

## Quick Commands

### Start the Demo

```text
"Let's run the Senzing quick demo"
```

### Define Your Problem

```text
"I want to start the Senzing bootcamp"
```

### Skip to Loading

```text
"I have SGES data ready, let's install Senzing and load it"
```

### Get Help

```text
"What is entity resolution?"
"How do I map my data?"
"Show me the bootcamp modules"
```

---

## What You'll Need

### For Demo (Path A)

- ✅ Nothing! Just ask the agent

### For Fast Track (Path B)

- ✅ SGES-formatted data file
- ✅ Senzing SDK installed (Module 0)
- ✅ Language runtime for your chosen language (Python, Java, C#, Rust, or TypeScript)

### For Complete Beginner (Path C)

- ✅ Raw data file (CSV, JSON, Excel, etc.)
- ✅ Language runtime for your chosen language
- ✅ Basic understanding of your data

### For Production (Path D - Full Bootcamp)

- ✅ All data sources identified
- ✅ PostgreSQL database (or plan to set up)
- ✅ Production environment access

---

## Quick Reference

### Module Overview

- **Module 1**: Quick Demo - Optional
- **Module 2**: Business Problem
- **Module 3**: Collect Data
- **Module 4**: Evaluate Quality
- **Module 5**: Map Data
- **Module 0**: Set Up SDK
- **Module 6**: Load Data
- **Module 7**: Multi-Source Orchestration
- **Module 8**: Query & Validate
- **Module 9**: Performance Testing
- **Module 10**: Security Hardening
- **Module 11**: Monitoring
- **Module 12**: Package & Deploy

### Skip Ahead Options

- Have SGES data? → Skip Module 5
- Senzing installed? → Skip Module 0
- Single source? → Skip Module 7
- Not production? → Skip Modules 9-12

---

## After Quick Start

### Next Steps

**After Demo (Path A)**:

1. Decide if entity resolution fits your use case
2. Choose Path B or C to work with your data
3. Or explore more sample datasets

**After Fast Track (Path B)**:

1. Review results and validate accuracy
2. Add more data sources (Module 3-5, 6-7)
3. Consider production deployment (Modules 9-12)

**After Complete Beginner (Path C)**:

1. Validate results with stakeholders
2. Add more data sources if needed
3. Plan production deployment

---

## Getting Help

### Ask the Agent

```text
"How do I start the bootcamp?"
"What's the fastest way to see results?"
"I'm stuck on Module 4, help!"
"Show me examples"
```

### Use MCP Tools

- `get_capabilities` - See all available tools
- `mapping_workflow` - Map your data
- `search_docs` - Find documentation
- `explain_error_code` - Diagnose errors

### Review Documentation

- `../../POWER.md` - Complete bootcamp overview
- `PROGRESS_TRACKER.md` - Track your progress
- `../modules/` - Detailed module guides
- `../../examples/` - Complete example projects

---

## Success Indicators

### You're Ready to Move On When

**After Demo**:

- ✅ You understand what entity resolution does
- ✅ You've seen duplicates automatically matched
- ✅ You can explain why records matched

**After Fast Track**:

- ✅ Your data is loaded into Senzing
- ✅ You can query for duplicates
- ✅ Results make sense for your use case

**After Complete Beginner**:

- ✅ All modules 2-6 and 8 complete
- ✅ Transformation and query programs work
- ✅ Results validated and documented

---

## Common Questions

**Q: Which path should I choose?**
A: Demo if exploring, Fast Track if experienced, Complete if learning.

**Q: Can I switch paths?**
A: Yes! Start with demo, then do Fast Track or Complete.

**Q: Do I need to install anything?**
A: Module 0 installs the Senzing SDK. You'll also need a runtime for your chosen language (Python, Java, C#, Rust, or TypeScript).

**Q: Can I use my own data?**
A: Yes for Fast Track and Complete. Demo uses sample data.

**Q: What if I get stuck?**
A: Ask the agent! That's what it's here for.

---

## Ready to Start?

Choose your path and tell the agent:

```text
"Let's run the quick demo"
"I want to do the 30-minute fast track"
"I'm ready for the complete beginner path"
"Show me the full bootcamp"
```

The agent will guide you through every step!

---

**Version**: 1.0.0
**Last updated**: 2026-03-23
