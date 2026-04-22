# Design Document

## Overview

The session resume flow is implemented entirely as an agent steering file (`senzing-bootcamp/steering/session-resume.md`). It is loaded when `config/bootcamp_progress.json` exists at session start, as determined by the session entry logic in `agent-instructions.md`. No application code is involved — the Agent follows the steering file's sequential instructions to restore context and resume the bootcamp.

## Architecture

### Session Entry Decision

```text
Session Start
  └─ Check config/bootcamp_progress.json
       ├─ EXISTS → load session-resume.md (this flow)
       └─ NOT EXISTS → load onboarding-flow.md
```

### Resume Sequence (5 steps)

```text
Step 1: Read All State Files
  ├─ config/bootcamp_progress.json  (modules, current module, data sources, db type)
  ├─ config/bootcamp_preferences.yaml  (language, path, detail_level)
  ├─ docs/bootcamp_journal.md  (if exists — narrative history)
  └─ config/mapping_state_*.json  (if any — in-progress mapping checkpoints)

Step 2: Load Language Steering
  └─ Map preferences.language → lang-{language}.md steering file

Step 3: Summarize and Confirm
  ├─ Display "🎓 Welcome back to the Senzing Bootcamp!" banner
  ├─ Show summary: path, language, completed modules, current module, db, data sources
  ├─ If mapping checkpoints exist, mention in-progress mapping state
  ├─ 👉 "Ready to continue with Module [N]?" → WAIT
  └─ Honor detail_level preference from preferences file

Step 4: Load Module Steering
  ├─ Continue → load current_module steering from Module Steering table
  ├─ Switch module → verify prerequisites via module-prerequisites.md, then load
  ├─ Switch path → follow path-switching logic in onboarding-flow.md
  └─ Start over → confirm, then load onboarding-flow.md

Step 5: Re-establish MCP Context
  └─ Call get_capabilities (required every new session)
```

### State Files

| File | Purpose |
| ---- | ------- |
| `config/bootcamp_progress.json` | Module completion state, current module, data sources, database type |
| `config/bootcamp_preferences.yaml` | Language, path, cloud provider, detail_level |
| `docs/bootcamp_journal.md` | Narrative session history |
| `config/mapping_state_*.json` | In-progress Module 5 mapping checkpoints |

### Language Steering Mapping

| Language | Steering File |
| -------- | ------------- |
| Python | `lang-python.md` |
| Java | `lang-java.md` |
| C# | `lang-csharp.md` |
| Rust | `lang-rust.md` |
| TypeScript | `lang-typescript.md` |

### Stale State Recovery

When `bootcamp_progress.json` appears inconsistent with actual project artifacts:

1. Run `python scripts/validate_module.py` to check artifact state
2. Display discrepancies to the Bootcamper
3. Offer to correct `bootcamp_progress.json` based on what actually exists
4. Resume from the last verifiably complete module

### Corrupted/Missing State Recovery

If `bootcamp_progress.json` or `bootcamp_preferences.yaml` is missing or unreadable, the Agent scans `src/`, `data/`, and `docs/` for evidence of completed work and offers to reconstruct the state files.

## Constraints

- No application code — the entire resume flow is steering-file-driven.
- `get_capabilities` must be called every session regardless of previous progress.
- The Agent must WAIT for user response after the summary before loading any module steering.
- Mapping checkpoints are only relevant for Module 5; their presence indicates an interrupted mapping session.
