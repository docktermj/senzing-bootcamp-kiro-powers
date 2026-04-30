# Senzing Bootcamp Quick Start

## What This Bootcamp Does

The bootcamp makes you comfortable generating code — with Kiro's help — that uses the Senzing SDK for entity resolution. You'll finish with running code that serves as the foundation for your real-world use of Senzing.

## Start

Say "start the bootcamp". The agent sets up your project, asks your language, gives you an overview of the modules, checks prerequisites, and presents four paths.

## Choose Your Path

Paths are not mutually exclusive — you can start with one and jump to another at any time. All completed modules carry forward.

| Path | For | Modules | Why Choose This |
| ---- | --- | ------- | --------------- |
| A) Quick Demo | First-time users — see entity resolution in action | 2 → 3 | Verify the technology works before investing more time |
| B) Fast Track | Have Senzing Entity Specification (SGES) data | 5 → 6 → 8 | Get straight to loading and querying |
| C) Complete Beginner | New users with raw data | 1 → 4 → 5 → 6 → 8 | Guided help through the entire process |
| D) Full Production | All modules through deployment | 1 → 2 → 3 → ... → 11 | Building something for production |

Module 2 (SDK Setup) is inserted automatically before any module that needs it.

**Don't have data?** Mock data can be generated at any point.

**Licensing:** Senzing includes a built-in evaluation license for 500 records. Bring your own license for more capacity.

## Quick Commands

```text
"Let's run the Senzing quick demo"          → Path A
"I have Entity Specification data ready, let's load it"     → Path B
"I want to start the bootcamp"              → Path C
"Show me the full bootcamp"                 → Path D
```

## What You Need

- A supported language runtime (Python, Java, C#, Rust, or TypeScript/Node.js)
- Prerequisites are checked automatically at startup

## Skip Ahead

- Have Entity Specification data? → Skip to Module 5 mapping phase
- SDK installed? → Skip Module 2
- Single source? → Skip Module 7
- Not deploying to production? → Skip Modules 8-11

## After Your Path

- **After A**: Decide if ER fits your use case, then try Path B or C with your data
- **After B**: Validate results, add more sources (Modules 4-5, 7), consider production (9-11)
- **After C**: Validate with stakeholders, plan production deployment
- **After D**: You're production-ready

## Getting Help

- Say "I'm stuck" — the agent loads troubleshooting guidance
- Use `explain_error_code` for any SENZ error codes
- Use `search_docs` for Senzing documentation
- Say "bootcamp feedback" to report issues
