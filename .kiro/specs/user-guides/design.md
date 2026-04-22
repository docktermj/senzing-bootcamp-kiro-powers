# Design Document

## Overview

Six standalone markdown guide files in `senzing-bootcamp/docs/guides/`, each addressing a distinct user need in the bootcamp lifecycle. No code components — pure documentation.

## File Structure

```
senzing-bootcamp/docs/guides/
├── QUICK_START.md              # Four learning paths, quick commands, skip-ahead options
├── ONBOARDING_CHECKLIST.md     # Prerequisites, what the agent automates, validation commands
├── PROGRESS_TRACKER.md         # Module status list (0–12), auto-sync via status.py
├── HOOKS_INSTALLATION_GUIDE.md # Auto/manual install, 11 hooks table, customization
├── AFTER_BOOTCAMP.md           # Maintenance cadence, scaling, new data, updates, advanced topics
└── COLLABORATION_GUIDE.md      # Team roles, git workflow, code review, data sharing
```

## Design Decisions

1. Each guide is self-contained with no cross-file dependencies beyond simple `see also` references.
2. Guides use task-list checkboxes (`- [ ]`) where actionable checklists are appropriate (onboarding, maintenance).
3. Progress Tracker integrates with `scripts/status.py --sync` to auto-generate from `config/bootcamp_progress.json`.
4. Quick Start presents paths as a comparison table for fast scanning.
5. Hooks Installation Guide covers four methods (agent, script, CLI, Kiro UI) to accommodate different user preferences and environments.
6. Collaboration Guide maps team roles directly to bootcamp module numbers for clear ownership.
