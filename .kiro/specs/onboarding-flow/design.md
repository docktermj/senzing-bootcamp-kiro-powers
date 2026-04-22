# Design Document

## Overview

The onboarding flow is implemented entirely as agent steering files — no application code. The Agent reads `onboarding-flow.md` at session start (when no `bootcamp_progress.json` exists) and follows its sequential instructions. Communication rules (👉 markers, Goldilocks checks, first-term explanations, one-question-at-a-time) are enforced by `agent-instructions.md`, which has `inclusion: always` and applies across all modules.

## Architecture

### Steering File Structure

```
senzing-bootcamp/steering/
├── onboarding-flow.md          # Main onboarding sequence (inclusion: manual)
├── agent-instructions.md       # Communication rules (inclusion: always)
├── project-structure.md        # Directory creation template (inclusion: auto)
├── session-resume.md           # Returning user flow
└── module-transitions.md       # Gate enforcement between modules
```

### Session Entry Logic

```
Session Start
  └─ Check config/bootcamp_progress.json
       ├─ EXISTS → load session-resume.md
       └─ NOT EXISTS → load onboarding-flow.md
```

### Onboarding Sequence (6 steps)

```
Step 0: Setup Preamble
  └─ Inform user: "you'll see me working, then a big WELCOME banner"

Step 1: Directory Structure (silent)
  ├─ Create project dirs (src/, data/, docs/, config/, etc.)
  ├─ Install hooks → .kiro/hooks/
  ├─ Copy GLOSSARY.md → docs/guides/
  └─ Generate steering files → .kiro/steering/
      ├─ product.md  (inclusion: always)
      ├─ tech.md     (inclusion: always)
      └─ structure.md (inclusion: auto)

Step 2: Language Selection
  ├─ Detect platform (platform.system())
  ├─ Query MCP server (get_capabilities / sdk_guide)
  ├─ Present supported languages with platform warnings
  ├─ 👉 "Which language?" → WAIT
  └─ Persist to config/bootcamp_preferences.yaml

Step 3: Prerequisite Check
  ├─ Check runtime (shutil.which())
  ├─ Check Senzing SDK import
  └─ Report only missing items

Step 4: Welcome Banner + Introduction
  ├─ Display 🎓🎓🎓 WELCOME TO THE SENZING BOOTCAMP 🎓🎓🎓 banner
  ├─ Present bootcamp overview (guided discovery, modules 0-12, mock data, paths)
  ├─ 👉 "Does this make sense? Any questions?" → WAIT
  └─ First-term explanations inline as terms appear

Step 5: Path Selection
  ├─ Present paths A/B/C/D with module sequences
  ├─ 👉 "Which path sounds right?" → WAIT
  ├─ Auto-insert Module 0 where SDK is needed
  └─ Persist to config/bootcamp_preferences.yaml
```

### Communication Rules (from agent-instructions.md)

| Rule | Mechanism | Scope |
|------|-----------|-------|
| One question at a time | WAIT markers in steering files | All modules |
| 👉 input-required marker | Prefix on all questions needing response | All modules |
| Goldilocks check | After modules 3, 6, 9 | Post-module |
| First-term explanation | Inline definition + glossary reference | First occurrence only |
| Detail level persistence | `config/bootcamp_preferences.yaml` → `detail_level` | Session-wide |

### Validation Gates

Gates are defined as a table in `onboarding-flow.md` (section "Validation Gates"). Each gate runs `validate_module.py --module N` and checks module-specific criteria before allowing progression. Results update `config/bootcamp_progress.json`.

### State Files

| File | Purpose |
|------|---------|
| `config/bootcamp_progress.json` | Module completion state, gate results |
| `config/bootcamp_preferences.yaml` | Language, path, detail_level |

### Path Switching

All completed modules carry forward. The Agent reads `bootcamp_progress.json`, compares completed modules against the new path's requirements, and resumes from the first incomplete module.

## Constraints

- No application code — the entire onboarding is steering-file-driven.
- MCP server is the authoritative source for language/platform support; no hardcoded assumptions.
- Glossary must be copied before Step 4 references it.
- Foundational steering files must include proper YAML frontmatter with `inclusion` and `description`.
