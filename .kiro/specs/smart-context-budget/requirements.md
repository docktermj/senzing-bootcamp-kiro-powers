# Requirements: Smarter Context Budget Warnings

## Overview

The context budget system warns at 60% and goes critical at 80%, but warnings are generic. This feature makes budget warnings actionable by suggesting specific steering files to unload and automatically pruning completed-module context to keep sessions smooth.

## Requirements

1. When the context budget reaches the warn threshold (60%), the agent identifies which loaded steering files are candidates for unloading based on: (a) the file belongs to a completed module, (b) the file hasn't been referenced in the last 5 turns, (c) the file is not the current module's steering
2. The warning message is actionable: "Context budget at 62%. I can free ~2,400 tokens by unloading Module 4 steering (completed). Want me to proceed, or keep it loaded?"
3. When the context budget reaches the critical threshold (80%), the agent automatically unloads completed-module steering files without asking, reporting what was unloaded
4. The agent maintains a `context_load_history` in memory (not persisted) tracking which steering files are currently loaded and when they were last referenced
5. Unloading a steering file means the agent stops referencing it for decisions but can reload it on demand if the bootcamper asks about a completed module
6. The retention priority order is enforced: agent-instructions.md > current module steering > language file > conversation-protocol > troubleshooting > completed module steering
7. The `measure_steering.py` script gains a `--simulate` flag that shows what would be loaded at each module and the cumulative token count, helping maintainers predict budget pressure
8. When suggesting unloads, the agent shows the token savings for each candidate file (from `steering-index.yaml` file_metadata)
9. If all completed-module files are already unloaded and the budget is still critical, the agent suggests splitting the current module's steering (if it has phases) and loading only the current phase
10. The budget warning behavior is documented in a new section of `agent-instructions.md` under Context Budget Management
11. The bootcamper can say "keep everything loaded" to suppress automatic unloading for the current session (stored transiently, not persisted)

## Non-Requirements

- This does not change the token counting methodology
- This does not modify steering file content
- This does not affect the split_threshold_tokens logic for file splitting
- This does not persist load history across sessions (it's rebuilt from progress state)
