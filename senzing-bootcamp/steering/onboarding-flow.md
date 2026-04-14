---
inclusion: manual
---

# Onboarding Flow

Load when starting a fresh bootcamp. Sequence: directory creation → language selection → prerequisites → introduction → path selection.

## 1. Directory Structure

Check if `src/`, `data/`, `docs/` exist. If not, load `project-structure.md` and create. Install hooks silently (copy `senzing-bootcamp/hooks/*.kiro.hook` to `.kiro/hooks/`). Generate foundational steering files (`product.md`, `tech.md`, `structure.md`) at `.kiro/steering/` with appropriate `inclusion` frontmatter. Do not narrate any of this to the user.

## 2. Language Selection

Query MCP (`get_capabilities`) for supported languages. Present list, ask user to choose. WAIT for response.

Persist to `config/bootcamp_preferences.yaml`. If file exists from previous session, confirm: "Last time you chose [language]. Continue or switch?"

Python is Linux-only. On macOS/Windows: suggest WSL2 or a different language. WSL2 setup: `wsl --install` (PowerShell), then install dev tools in Ubuntu, project lives in WSL2 filesystem.

Load language steering file immediately after confirmation (`lang-python.md`, `lang-java.md`, etc.).

## 3. Prerequisite Check

Detect platform (`platform.system()`). Check language runtime with `shutil.which()` — cross-platform, not `command -v`. Check for Senzing SDK import. Present results only if something is missing. Surface all missing deps here — don't discover them one at a time later.

**If the Senzing SDK is already installed and working (V4.0+):** Tell the user: "Senzing SDK is already installed." When Module 0 is reached (either explicitly or auto-inserted), the module's Step 1 check will detect this and skip installation. Do not re-install.

## 4. Bootcamp Introduction

Present the overview before path selection. Cover all points naturally:

- Goal: comfortable generating Senzing SDK code. Finish with running code as foundation for real use.
- Module overview table (0-12): what each does and why it matters
- Mock data available anytime. Three sample datasets: Las Vegas (customers), London (persons), Moscow (organizations)
- Built-in 500-record eval license; bring your own for more
- Paths let you skip to what matters

Ask: "Does this outline make sense? Any questions before we choose a path?" WAIT for response.

## 5. Path Selection

Present paths — not mutually exclusive, all completed modules carry forward:

- **A) Quick Demo** — 0→1. Verify technology works. One session.
- **B) Fast Track** — 5→6→8. Have SGES data. Straight to loading/querying.
- **C) Complete Beginner** — 2→3→4→5→6→8. From scratch with raw data.
- **D) Full Production** — All 0-12. Building for production.

Module 0 inserted automatically before any module needing SDK.

Interpreting responses: "A"/"demo"→Module 1, "B"/"fast"→Module 5, "C"/"beginner"→Module 2, "D"/"full"→Module 0. Bare number→clarify letter vs module.

## Switching Paths

All completed modules carry forward. Read `bootcamp_progress.json`, show new path requirements vs. done, update preferences, resume from first incomplete module.

## Changing Language

Update preferences. Warn: existing code in `src/` must be regenerated. Data/docs/config unaffected. Don't mix languages.

## Validation Gates

Run `validate_module.py --module N` before proceeding. Update `bootcamp_progress.json` and `bootcamp_preferences.yaml`. Every 3 modules: progress bar.

Gate checks:

| Gate  | Requires                                                                           |
|-------|------------------------------------------------------------------------------------|
| 0→1   | SDK installed, DB configured, test passes                                          |
| 1→2   | Demo completed or skipped                                                          |
| 2→3   | Problem documented, sources identified, criteria defined                           |
| 3→4   | Sources collected, files in `data/raw/`                                            |
| 4→5   | Sources evaluated, SGES compliance determined                                      |
| 5→6   | Sources mapped, programs tested, quality >70%                                      |
| 6→7   | Sources loaded, no critical errors                                                 |
| 7→8   | All sources orchestrated (or single source)                                        |
| 8→9   | Queries answer business problem, results validated. Load `cloud-provider-setup.md` |
| 9→10  | Baselines captured, bottlenecks documented                                         |
| 10→11 | Security checklist complete, no critical vulns                                     |
| 11→12 | Monitoring configured, health checks passing                                       |
