# Senzing Bootcamp Quick Start

## Start

Say "start the bootcamp". The agent sets up your project, asks your language, checks prerequisites, and presents four paths.

## Choose Your Path

| Path | For | Modules |
| ---- | --- | ------- |
| A) Quick Demo | First-time users — see entity resolution in action | 0 → 1 |
| B) Fast Track | Have Senzing-ready (SGES) data | 0 → 5 → 6 |
| C) Complete Beginner | New users with raw data | 2 → 3 → 4 → 5 → 0 → 6 → 8 |
| D) Full Production | All modules through deployment | 0 → 1 → 2 → ... → 12 |

Module 0 (SDK Setup) is inserted automatically before any module that needs it.

## Quick Commands

```text
"Let's run the Senzing quick demo"          → Path A
"I have SGES data ready, let's load it"     → Path B
"I want to start the bootcamp"              → Path C
"Show me the full bootcamp"                 → Path D
```

## What You Need

- A supported language runtime (Python, Java, C#, Rust, or TypeScript/Node.js)
- Prerequisites are checked automatically at startup

## Skip Ahead

- Have SGES data? → Skip Module 5
- SDK installed? → Skip Module 0
- Single source? → Skip Module 7
- Not deploying to production? → Skip Modules 9-12

## After Your Path

- **After A**: Decide if ER fits your use case, then try Path B or C with your data
- **After B**: Validate results, add more sources (Modules 3-5, 7), consider production (9-12)
- **After C**: Validate with stakeholders, plan production deployment
- **After D**: You're production-ready

## Getting Help

- Say "I'm stuck" — the agent loads troubleshooting guidance
- Use `explain_error_code` for any SENZ error codes
- Use `search_docs` for Senzing documentation
- Say "bootcamp feedback" to report issues
