---
inclusion: auto
---

# Repository Organization

All files belong in `senzing-bootcamp/` — the distributed power directory.

## File Placement

| Content Type | Location | Audience |
|---|---|---|
| Module docs | `senzing-bootcamp/docs/modules/` | Users |
| User guides | `senzing-bootcamp/docs/guides/` | Users |
| Feedback templates | `senzing-bootcamp/docs/feedback/` | Users |
| Agent steering | `senzing-bootcamp/steering/` | Agents |
| Agent policies | `senzing-bootcamp/docs/policies/` | Agents |
| Code templates | `senzing-bootcamp/templates/` | Users |
| Example projects | `senzing-bootcamp/examples/` | Users |
| Hooks | `senzing-bootcamp/hooks/` | Agents |
| Scripts | `senzing-bootcamp/scripts/` | Both |
| Tests | `senzing-bootcamp/tests/` | Developers |
| Power config | `senzing-bootcamp/` root | Framework |

## Rules

- Never place dev notes, build artifacts, or historical files in the repo — use git history.
- Power config files (`POWER.md`, `mcp.json`, `icon.png`) stay at `senzing-bootcamp/` root.
- Hook tests that validate real hook files go in `tests/` (repo root), not `senzing-bootcamp/tests/`.
