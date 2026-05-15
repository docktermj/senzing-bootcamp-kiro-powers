# Senzing Bootcamp Quick Start

## What This Bootcamp Does

The bootcamp makes you comfortable generating code — with Kiro's help — that uses the Senzing SDK for entity resolution. You'll finish with running code that serves as the foundation for your real-world use of Senzing.

## Start

Say "start the bootcamp". The agent sets up your project, asks your language, gives you an overview of the modules, checks prerequisites, and presents two tracks.

## Choose Your Track

Tracks are not mutually exclusive — you can start with one and switch at any time. All completed modules carry forward.

| Track | For | Modules | Why Choose This |
| ----- | --- | ------- | --------------- |
| Core Bootcamp | New users building an entity resolution solution | 1, 2, 3, 4, 5, 6, 7 | Recommended foundation covering problem definition through query/visualize |
| Advanced Topics | Users who need production-readiness | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 | Adds performance, security, monitoring, and deployment on top of core |

Module 2 (SDK Setup) is inserted automatically before any module that needs it.

**Don't have data?** Senzing provides [CORD (Collections Of Relatable Data)](https://senzing.com/senzing-ready-data-collections-cord/) — curated, real-world-like datasets designed for entity resolution evaluation. Use the `get_sample_data` tool to download a CORD dataset (Las Vegas, London, or Moscow). If CORD data doesn't meet your specific needs, test data can be generated as a fallback.

**Licensing:** Senzing includes a built-in evaluation license for 500 records. Bring your own license for more capacity.

## Quick Commands

```text
"I want to start the bootcamp"              → Core Bootcamp
"Let's run Senzing system verification"     → Core Bootcamp, Module 3
"Show me the full bootcamp"                 → Advanced Topics
```

## What You Need

- A supported language runtime (Python, Java, C#, Rust, or TypeScript/Node.js)
- Prerequisites are checked automatically at startup

**Windows users:** Use `python` instead of `python3` for all commands. We recommend Windows Terminal or PowerShell 7 for proper Unicode support (the bootcamp uses emoji in banners). Install with `winget install Microsoft.WindowsTerminal`. If using TypeScript, you'll also need Visual Studio Build Tools for native addon compilation.

## Skip Ahead

- Have Entity Specification data? → Skip to Module 5 mapping phase
- SDK installed? → Skip Module 2
- Single source? → Skip Module 7
- Not deploying to production? → Skip Modules 8-11

## After Your Track

- **After Core Bootcamp**: Validate with stakeholders, plan production deployment via Advanced Topics
- **After Advanced Topics**: You're production-ready

## Getting Help

- Say "I'm stuck" — the agent loads troubleshooting guidance
- Use `explain_error_code` for any SENZ error codes
- Use `search_docs` for Senzing documentation
- Say "bootcamp feedback" to report issues
