# Senzing Bootcamp Onboarding Checklist

The bootcamp handles most setup automatically — just say "start the bootcamp" and the agent takes care of directory creation, prerequisite checks, and hook installation. This checklist is for reference if you want to verify readiness beforehand.

## Before You Start

- [ ] A supported language runtime installed (Python, Java, C#, Rust, or TypeScript/Node.js) — the agent checks this automatically
- [ ] Git installed (optional but recommended)
- [ ] 10 GB+ free disk space (50 GB+ for production)
- [ ] 4 GB+ RAM (8 GB+ recommended)

## Data (Optional — Not Required to Start)

- [ ] Data sources identified (or plan to use sample data)
- [ ] Sample data extracted (100-1000 records) if using your own data
- [ ] Data privacy requirements understood (GDPR, HIPAA, etc.)

If you don't have data ready, the bootcamp provides three sample datasets (Las Vegas, London, Moscow) and can generate mock data at any point.

## What the Agent Does for You

When you say "start the bootcamp," the agent automatically:

1. Creates the project directory structure (`src/`, `data/`, `docs/`, `database/`, etc.)
2. Installs bootcamp hooks for quality checks
3. Detects your platform and queries the Senzing MCP server for supported languages
4. Checks prerequisites and surfaces anything missing
5. Presents the bootcamp overview and answers your questions
6. Lets you choose a learning path

You don't need to do any of this manually.

## Quick Validation (Optional)

```bash
# Check your language runtime
python3 --version    # or java --version, dotnet --version, rustc --version, node --version

# Check git
git --version

# Check disk space (Python)
python3 -c "import shutil; u=shutil.disk_usage('.'); print(f'{u.free/(1024**3):.0f} GB free')"
```

## Ready?

Say "start the bootcamp" — the agent guides you from there. See `QUICK_START.md` for path options, or `GLOSSARY.md` if you encounter unfamiliar terms.
