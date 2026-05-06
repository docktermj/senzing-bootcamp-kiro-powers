# Design: Smarter Context Budget Warnings

## Overview

When context budget thresholds are reached, the agent provides actionable suggestions — identifying specific steering files to unload, showing token savings, and automatically pruning completed-module context at critical levels.

## Context Load Tracking

The agent maintains a mental model (not persisted) of which steering files are currently loaded:

```
Loaded files (working memory):
- agent-instructions.md (always loaded, 2100 tokens)
- module-06-load-data.md (current module, 3200 tokens)
- lang-python.md (language file, 1800 tokens)
- conversation-protocol.md (always loaded, 1500 tokens)
- module-04-data-collection.md (completed, 2400 tokens) ← candidate
- module-05-data-quality-mapping.md (completed, 2800 tokens) ← candidate
```

## Unload Candidate Selection

A file is a candidate for unloading when ALL of these are true:
1. It belongs to a completed module (not the current module)
2. It hasn't been referenced in the last 5 turns
3. It's not in the retention priority list's top tier

## Retention Priority Order

```
1. agent-instructions.md (never unload)
2. Current module steering (never unload while in that module)
3. Language file (never unload)
4. conversation-protocol.md (never unload)
5. common-pitfalls.md / troubleshooting (unload only at critical)
6. Completed module steering (first to unload)
```

## Warn Threshold Behavior (60%)

When cumulative loaded tokens reach 60% of reference_window:

```
⚠️ Context budget at 62%. I can free approximately:
- ~2,400 tokens by unloading Module 4 steering (completed)
- ~2,800 tokens by unloading Module 5 steering (completed)

👉 Want me to unload completed module context, or keep everything loaded?
```

The agent waits for the bootcamper's response before acting.

## Critical Threshold Behavior (80%)

When cumulative loaded tokens reach 80% of reference_window:

```
🔴 Context budget at 82% — automatically unloading completed module steering:
- Unloaded: module-04-data-collection.md (freed ~2,400 tokens)
- Unloaded: module-05-data-quality-mapping.md (freed ~2,800 tokens)

These can be reloaded on demand if you need to revisit earlier modules.
```

No question asked — automatic action to prevent context overflow.

## "Keep Everything Loaded" Override

If the bootcamper says "keep everything loaded" (or similar), the agent:
1. Suppresses automatic unloading for the current session
2. Does NOT persist this preference (it resets on session resume)
3. Still shows warnings but doesn't act on them

## measure_steering.py --simulate

```
$ python measure_steering.py --simulate
Module 1: agent-instructions(2100) + module-01(1800) + lang-python(1800) = 5700 tokens (2.9%)
Module 2: agent-instructions(2100) + module-02(2200) + lang-python(1800) = 6100 tokens (3.1%)
...
Module 7: agent-instructions(2100) + module-07(3500) + lang-python(1800) + completed[4,5,6](8400) = 15800 tokens (7.9%)
Module 11: agent-instructions(2100) + module-11(2800) + lang-python(1800) + completed[1-10](28000) = 34700 tokens (17.4%)

Peak without unloading: 34,700 tokens (17.4% of 200k reference window)
Peak with unloading: 8,700 tokens (4.4% of 200k reference window)
```

## Phase-Based Splitting Suggestion

If all completed modules are unloaded and budget is still critical (unlikely but possible with very large current-module files):

```
🔴 Budget still critical after unloading completed modules.
Module 9 has phases — I'll load only Phase A (current) instead of the full file.
Freed ~1,200 tokens by unloading Phase B content.
```

## Files Modified

- `senzing-bootcamp/steering/agent-instructions.md` — add Context Budget Management section
- `senzing-bootcamp/scripts/measure_steering.py` — add `--simulate` flag

## Testing

- Unit test: agent-instructions.md contains "Context Budget Management" section
- Unit test: measure_steering.py accepts `--simulate` flag
- Unit test: --simulate output contains per-module token calculations
- Property test: retention priority order is documented correctly
- Property test: unload candidates are always from completed modules only
